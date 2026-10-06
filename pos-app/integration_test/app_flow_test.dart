// Runs the REAL app on an emulator/device against the running backend, with
// dev "simulate tap" instead of NFC. Start with tool/run_integration.sh
// (it creates a fixture and passes the tokens as --dart-define).
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:path_provider/path_provider.dart';
import 'package:schooldimes_pos/app/app.dart';
import 'package:schooldimes_pos/core/security/pin_verifier.dart';

const canteenToken = String.fromEnvironment('SD_CANTEEN_TOKEN');
const cardUid = String.fromEnvironment('SD_CARD_UID');
const pin = String.fromEnvironment('SD_PIN', defaultValue: '2468');

const vector = r'pbkdf2_sha256$870000$Zp1sAltValue0001$QjRoWpfHmhZknMcby7lVqmy5XHN+EwrR+Avul8TiC08=';

Future<void> pumpUntil(WidgetTester t, Finder f, {Duration timeout = const Duration(seconds: 60)}) async {
  final end = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(end)) {
    await t.pump(const Duration(milliseconds: 250));
    if (f.evaluate().isNotEmpty) return;
  }
  final texts = find.byType(RichText, skipOffstage: false).evaluate().map((e) => (e.widget as RichText).text.toPlainText()).join(' | ');
  throw TestFailure('Timed out waiting for $f. On screen: $texts');
}

Finder productTile() => find.byWidgetPredicate((w) => w.key is ValueKey && RegExp(r'^product-\d+$').hasMatch('${(w.key as ValueKey).value}'));

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('native PBKDF2 (Android) matches the backend vectors', (t) async {
    final native = PinVerifier(preferNative: true); // method channel -> PBKDF2WithHmacSHA256
    final sw = Stopwatch()..start();
    expect(await native.verify('1234', vector), isTrue);
    debugPrint('native 870k-iteration PIN check: ${sw.elapsedMilliseconds} ms');
    expect(await native.verify('1235', vector), isFalse);
  });

  testWidgets('provision → online sale (simulated tap + PIN) → receipt → staff summary', (t) async {
    expect(canteenToken, isNotEmpty, reason: 'run via tool/run_integration.sh');
    // a fresh device: no identity, no database
    await const FlutterSecureStorage().deleteAll();
    final dir = await getApplicationSupportDirectory();
    for (final f in dir.listSync()) {
      if (f.path.contains('schooldimes_pos.db')) f.deleteSync();
    }

    await t.pumpWidget(const ProviderScope(child: PosApp()));
    await pumpUntil(t, find.byKey(const Key('setup-token')));
    await t.enterText(find.byKey(const Key('setup-url')), 'http://10.0.2.2:8000');
    await t.enterText(find.byKey(const Key('setup-token')), canteenToken);
    await t.enterText(find.byKey(const Key('setup-pin')), '9999');
    await t.enterText(find.byKey(const Key('setup-pin2')), '9999');
    await t.tap(find.byKey(const Key('setup-submit')));
    await pumpUntil(t, find.byKey(const Key('charge')));
    FocusManager.instance.primaryFocus?.unfocus(); // close the keyboard left from setup
    await t.pump(const Duration(milliseconds: 300));

    // The first background sync re-writes the product list right after
    // setup; retry until the tap lands on the current grid.
    String cartTotal() => (find.byKey(const Key('cart-total'), skipOffstage: false).evaluate().single.widget as Text).data!;
    for (var i = 0; i < 20 && cartTotal() == 'UGX 0'; i++) {
      await pumpUntil(t, productTile());
      await t.tap(productTile().first, warnIfMissed: false);
      await t.pump(const Duration(milliseconds: 500));
    }
    expect(cartTotal(), isNot('UGX 0'));
    await t.tap(find.byKey(const Key('charge')));
    await pumpUntil(t, find.byKey(const Key('simulate-uid')));
    FocusManager.instance.primaryFocus?.unfocus();
    await t.enterText(find.byKey(const Key('simulate-uid')), cardUid);
    await t.tap(find.byKey(const Key('simulate-tap')));
    await pumpUntil(t, find.byKey(const Key('pin-dots')));
    for (final d in pin.split('')) {
      await t.tap(find.byKey(Key('key-$d')));
      await t.pump();
    }
    await t.tap(find.byKey(const Key('key-done')));
    await pumpUntil(t, find.byKey(const Key('confirm-sale')), timeout: const Duration(seconds: 90));
    await t.tap(find.byKey(const Key('confirm-sale')));
    await pumpUntil(t, find.byKey(const Key('receipt-done')));
    expect(find.byKey(const Key('receipt-balance')), findsOneWidget);
    expect(find.byKey(const Key('offline-badge')), findsNothing); // the emulator is online
    await t.tap(find.byKey(const Key('receipt-done')));
    await t.pump(const Duration(milliseconds: 500));

    await t.tap(find.byIcon(Icons.admin_panel_settings));
    await pumpUntil(t, find.byKey(const Key('key-9')));
    for (var i = 0; i < 4; i++) {
      await t.tap(find.byKey(const Key('key-9')));
      await t.pump();
    }
    await t.tap(find.byKey(const Key('key-done')));
    await pumpUntil(t, find.byKey(const Key('today-sales')));
    expect(find.textContaining('1 sale'), findsOneWidget);
    debugPrint('INTEGRATION OK');
  }, timeout: const Timeout(Duration(minutes: 5)));
}

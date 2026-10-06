// The real parent app on an emulator/device against the running backend.
// Run with tool/run_integration.sh: it confirms the deposit this test
// creates with `manage.py mock_webhook <reference>` (mock aggregator).
import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:schooldimes_parent/app/app.dart';
import 'package:schooldimes_parent/app/providers.dart';
import 'package:schooldimes_parent/core/money/money.dart';

Future<void> pumpUntil(WidgetTester t, Finder f, {Duration timeout = const Duration(seconds: 60)}) async {
  final end = DateTime.now().add(timeout);
  while (DateTime.now().isBefore(end)) {
    await t.pump(const Duration(milliseconds: 250));
    if (f.evaluate().isNotEmpty) return;
  }
  final texts = find.byType(RichText, skipOffstage: false).evaluate().map((e) => (e.widget as RichText).text.toPlainText()).join(' | ');
  throw TestFailure('Timed out waiting for $f. On screen: $texts');
}

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();

  testWidgets('login → dashboard → top-up → mock_webhook confirm → balance updated', (t) async {
    await const FlutterSecureStorage().deleteAll();
    final cache = await createDashboardCache();
    await cache.clear();
    await t.pumpWidget(ProviderScope(overrides: [dashboardCacheProvider.overrideWithValue(cache)], child: const ParentApp()));

    await pumpUntil(t, find.byKey(const Key('login-email')));
    await t.enterText(find.byKey(const Key('login-email')), 'parent1@schooldimes.test');
    await t.enterText(find.byKey(const Key('login-password')), 'pw123456');
    await t.tap(find.byKey(const Key('login-submit')));
    // generous: the first request after an emulator cold start can be slow
    await pumpUntil(t, find.byKey(const Key('balance-1')), timeout: const Duration(minutes: 2));
    FocusManager.instance.primaryFocus?.unfocus();
    final before = Money.parse((t.widget<Text>(find.byKey(const Key('balance-1'))).data!).replaceAll(RegExp(r'[^0-9.]'), ''));

    await t.tap(find.byKey(const Key('topup-1')));
    await pumpUntil(t, find.byKey(const Key('topup-amount')));
    await t.enterText(find.byKey(const Key('topup-amount')), '5000');
    FocusManager.instance.primaryFocus?.unfocus();
    await t.pump(const Duration(milliseconds: 300));
    await t.tap(find.byKey(const Key('topup-pay')));
    await pumpUntil(t, find.textContaining('Reference SD-DEP-'));
    final ref = (t.widget<Text>(find.textContaining('Reference SD-DEP-')).data!).replaceFirst('Reference ', '');
    debugPrint('DEPOSIT_REF=$ref');

    // tool/run_integration.sh now runs mock_webhook; the app keeps polling
    await pumpUntil(t, find.text('Paid — the money is on the card'), timeout: const Duration(minutes: 2));
    await t.tap(find.text('Done'));
    await pumpUntil(t, find.byKey(const Key('balance-1')));
    final expected = (before + Money.parse('5000')).format();
    await pumpUntil(t, find.text(expected), timeout: const Duration(seconds: 30));
    debugPrint('PARENT INTEGRATION OK: ${before.format()} -> $expected');
  }, timeout: const Timeout(Duration(minutes: 5)));
}

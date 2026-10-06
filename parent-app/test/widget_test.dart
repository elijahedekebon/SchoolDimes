import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_parent/app/app.dart';
import 'package:schooldimes_parent/app/app_lock.dart';
import 'package:schooldimes_parent/app/providers.dart';
import 'package:schooldimes_parent/core/storage/token_store.dart';

import 'support/fake_api.dart';
import 'support/memory_cache.dart';

class _NoLock extends AppLockNotifier {
  @override
  Future<bool> build() async => false;
}

Future<FakeParentApi> pumpApp(WidgetTester t, {bool signedIn = true, FakeParentApi? api}) async {
  final fake = api ?? FakeParentApi();
  final tokens = MemoryTokenStore();
  if (signedIn) await tokens.save('a', 'r');
  await t.pumpWidget(ProviderScope(
    overrides: [
      parentApiProvider.overrideWithValue(fake),
      tokenStoreProvider.overrideWithValue(tokens),
      dashboardCacheProvider.overrideWithValue(MemoryDashboardCache()),
      appLockProvider.overrideWith(_NoLock.new),
    ],
    child: const ParentApp(),
  ));
  await t.pumpAndSettle();
  return fake;
}

void main() {
  testWidgets('login: wrong password shows the backend message; right one opens the dashboard', (t) async {
    final api = FakeParentApi()..wrongPasswordFor = 'bad@x.test';
    await pumpApp(t, signedIn: false, api: api);
    await t.enterText(find.byKey(const Key('login-email')), 'bad@x.test');
    await t.enterText(find.byKey(const Key('login-password')), 'nope');
    await t.tap(find.byKey(const Key('login-submit')));
    await t.pumpAndSettle();
    expect(find.text('No active account found with the given credentials'), findsOneWidget);

    await t.enterText(find.byKey(const Key('login-email')), 'parent1@schooldimes.test');
    await t.enterText(find.byKey(const Key('login-password')), 'pw123456');
    await t.tap(find.byKey(const Key('login-submit')));
    await t.pumpAndSettle();
    expect(find.byKey(const Key('child-1')), findsOneWidget);
  });

  testWidgets('dashboard: one card per child with balances, card status, itemized purchase and tip', (t) async {
    await pumpApp(t);
    expect(find.byKey(const Key('child-1')), findsOneWidget);
    expect(find.byKey(const Key('child-2')), findsOneWidget);
    expect(find.text('UGX 25,300'), findsOneWidget);
    expect(find.text('Card active'), findsNWidgets(2));
    expect(find.text('1× Rice & beans'), findsNWidgets(2));
    await t.scrollUntilVisible(find.text('Needs vs. wants'), 300);
    expect(find.text('Needs vs. wants'), findsOneWidget);
  });

  testWidgets('freeze a card in two taps (button + confirm)', (t) async {
    final api = await pumpApp(t);
    await t.tap(find.byKey(const Key('freeze-1')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(const Key('confirm')));
    await t.pumpAndSettle();
    expect(api.freezeCalls, 1);
    expect(find.text('Card frozen'), findsOneWidget);
    expect(find.text('Unfreeze card'), findsOneWidget);
  });

  testWidgets('top-up: instructions, status polling to confirmed, balance updated', (t) async {
    final api = await pumpApp(t);
    api.depositStatusSequence = ['pending', 'confirmed'];
    await t.tap(find.byKey(const Key('topup-1')));
    await t.pumpAndSettle();
    await t.enterText(find.byKey(const Key('topup-amount')), '5000');
    await t.tap(find.byKey(const Key('topup-pay')));
    await t.pump();
    await t.pump(const Duration(milliseconds: 100));
    expect(find.text('Approve the payment on your phone.'), findsOneWidget);
    // two polls, 3 s apart
    await t.pump(const Duration(seconds: 4));
    await t.pumpAndSettle();
    expect(find.byKey(const Key('deposit-status')), findsOneWidget);
    expect(find.text('Paid — the money is on the card'), findsOneWidget);
    await t.tap(find.text('Done'));
    await t.pumpAndSettle();
    expect(find.text('UGX 30,300'), findsOneWidget);
    expect(api.depositsCreated, 1);
  });

  testWidgets('report a problem from a transaction raises a dispute with its target', (t) async {
    final api = await pumpApp(t);
    await t.tap(find.byKey(const Key('txn-101')).first);
    await t.pumpAndSettle();
    await t.tap(find.byKey(const Key('report-problem')));
    await t.pumpAndSettle();
    await t.tap(find.byKey(const Key('reason-duplicate')));
    await t.tap(find.byKey(const Key('dispute-send')));
    await t.pumpAndSettle();
    expect(api.raisedDisputes.single, {'pos_transaction': 88, 'reason_category': 'duplicate', 'description': ''});
  });

  testWidgets('offline: the last dashboard is shown read-only with "last updated"', (t) async {
    final cache = MemoryDashboardCache();
    await cache.save(await FakeParentApi().dashboard());
    final offline = FakeOfflineParentApi();
    final tokens = MemoryTokenStore();
    await tokens.save('a', 'r');
    await t.pumpWidget(ProviderScope(
      overrides: [
        parentApiProvider.overrideWithValue(offline),
        tokenStoreProvider.overrideWithValue(tokens),
        dashboardCacheProvider.overrideWithValue(cache),
        appLockProvider.overrideWith(_NoLock.new),
      ],
      child: const ParentApp(),
    ));
    await t.pumpAndSettle();
    expect(find.byKey(const Key('offline-banner')), findsOneWidget);
    expect(find.text('UGX 25,300'), findsOneWidget);
    expect(find.byKey(const Key('topup-1')), findsNothing); // read-only
  });
}

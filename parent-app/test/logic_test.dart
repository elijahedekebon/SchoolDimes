import 'dart:io';

import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_parent/core/api/api_client.dart';
import 'package:schooldimes_parent/core/money/money.dart';
import 'package:schooldimes_parent/features/dashboard/dashboard_cache.dart';
import 'package:schooldimes_parent/features/notifications/deep_links.dart';
import 'package:schooldimes_parent/features/topup/deposit_flow.dart';

import 'support/fake_api.dart';

void main() {
  group('money formatting (no floats)', () {
    test('UGX', () {
      expect(Money.parse('25300.00').format(), 'UGX 25,300');
      expect(Money.parse('1500.5').format(), 'UGX 1,500.50');
      expect((Money.parse('0.10') + Money.parse('0.20')).toApi(), '0.30');
    });
  });

  group('deep links', () {
    test('low balance opens a pre-filled top-up from the payload', () {
      expect(
        deepLinkFor('low_balance', {
          'student_id': 1,
          'wallet_id': 1,
          'action': {'type': 'top_up', 'student_id': 1, 'wallet_id': 31, 'suggested_amount': '5000'}
        }),
        const DeepLink(Destination.topUp, studentId: 1, walletId: 31, suggestedAmount: '5000'),
      );
    });
    test('each event type routes to its screen', () {
      expect(deepLinkFor('deposit_failed', {'deposit_id': 9}).destination, Destination.depositStatus);
      expect(deepLinkFor('deposit_failed', {'deposit_id': 9}).id, 9);
      expect(deepLinkFor('card_frozen', {'student_id': 2, 'card_id': 3}), const DeepLink(Destination.card, studentId: 2, id: 3));
      expect(deepLinkFor('dispute_status_changed', {'dispute_id': 4}).destination, Destination.dispute);
      expect(deepLinkFor('recurring_topup_paused', {'recurring_topup_id': 5}).id, 5);
      expect(deepLinkFor('gift_received', {'student_id': 1}).destination, Destination.childHistory);
      expect(deepLinkFor('savings_goal_reached', {'student_id': 1}).destination, Destination.savings);
      expect(deepLinkFor('p2p_transfer_received', {'student_id': 1}).destination, Destination.p2p);
      expect(deepLinkFor('pooled_fund_contribution_confirmed', {'fund_id': 3}).id, 3);
      expect(deepLinkFor('data_request_updated', {'request_id': 2}).destination, Destination.privacy);
      expect(deepLinkFor('something_new', {}).destination, Destination.inbox);
    });
  });

  group('idempotent top-up retry', () {
    test('a retry after a network error reuses the key; the server answers with the same deposit', () async {
      final api = FakeParentApi()..failNextDeposit = ApiException(network: true);
      final draft = DepositDraft();
      await expectLater(draft.submit(api, walletId: 1, amount: '5000', channel: 'momo'), throwsA(isA<ApiException>()));
      final first = await draft.submit(api, walletId: 1, amount: '5000', channel: 'momo');
      final again = await draft.submit(api, walletId: 1, amount: '5000', channel: 'momo');
      expect(api.depositKeys.toSet(), hasLength(1));
      expect(again['id'], first['id']);
      expect(api.depositsCreated, 1);
      draft.startOver();
      await draft.submit(api, walletId: 1, amount: '5000', channel: 'momo');
      expect(api.depositsCreated, 2);
    });

    test('polling stops when the deposit leaves pending and survives network blips', () async {
      final api = FakeParentApi();
      final d = await DepositDraft().submit(api, walletId: 1, amount: '5000', channel: 'momo');
      api.depositStatusSequence = ['pending', 'network', 'pending', 'confirmed'];
      final seen = await pollDeposit(api, d['id'] as int, every: Duration.zero).map((x) => x['status']).toList();
      expect(seen, ['pending', 'pending', 'confirmed']);
    });
  });

  test('dashboard cache round-trip', () async {
    final dir = Directory.systemTemp.createTempSync('sdparent');
    final cache = DashboardCache(dir);
    await cache.save({'students': []}, at: DateTime.utc(2026, 10, 6, 8));
    final (data, at) = (await cache.load())!;
    expect(data, {'students': []});
    expect(at, DateTime.utc(2026, 10, 6, 8));
    dir.deleteSync(recursive: true);
  });
}

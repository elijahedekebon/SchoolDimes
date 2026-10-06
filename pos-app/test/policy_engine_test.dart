// Mirrors backend/policies/tests.py::TestAuthorizeDebit case for case, plus
// one test per reason code. The engine must agree with debit_violations().
import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_pos/core/money/money.dart';
import 'package:schooldimes_pos/features/policy/policy_engine.dart';

Money m(String v) => Money.parse(v);

// catalog fixture from the backend test: snacks=1, sugary=2, meals=3; soda=10 (sugary), chips=11 (snacks), rice=12 (meals)
const snacks = 1, sugary = 2, meals = 3;
const soda = 10, chips = 11, rice = 12;
SaleLine line(int product, int category, String price) => SaleLine(productId: product, categoryId: category, quantity: 1, unitPrice: m(price));

CardState card({
  String status = 'active',
  String balance = '10000',
  String today = '0',
  String week = '0',
  String ceiling = '2000',
  CardPolicy policy = const CardPolicy(),
}) =>
    CardState(status: status, balance: m(balance), todaySpend: m(today), weekSpend: m(week), offlineSpendCeiling: m(ceiling), policy: policy);

void main() {
  group('mirrors TestAuthorizeDebit.test_caps_categories_items', () {
    final policy = CardPolicy(
      dailySpendCap: m('4000'),
      perTransactionCap: m('3500'),
      blockedCategoryIds: {sugary},
      blockedProductIds: {chips},
    );
    test('rice 3000 allowed', () => expect(purchaseViolations(card(policy: policy), m('3000'), [line(rice, meals, '3000')]), isEmpty));
    test('3600 over per-transaction cap', () => expect(purchaseViolations(card(policy: policy), m('3600'), []).first, 'per_transaction_cap_exceeded'));
    test('soda: category blocked', () => expect(purchaseViolations(card(policy: policy), m('1500'), [line(soda, sugary, '1500')]).first, 'category_blocked'));
    test('chips: item blocked', () => expect(purchaseViolations(card(policy: policy), m('1000'), [line(chips, snacks, '1000')]).first, 'item_blocked'));
    test('20000: insufficient funds first (strict, as online)', () {
      expect(purchaseViolations(card(policy: policy), m('20000'), [], strictBalance: true).take(1), ['insufficient_funds']);
    });
    test('after a 3000 sale today, 1500 breaks the 4000 daily cap but 1000 is fine', () {
      expect(purchaseViolations(card(policy: policy, today: '3000'), m('1500'), []).first, 'daily_cap_exceeded');
      expect(purchaseViolations(card(policy: policy, today: '3000'), m('1000'), []), isEmpty);
    });
  });

  test('mirrors test_weekly_cap: 1500 over a 1000 weekly cap', () {
    expect(purchaseViolations(card(policy: CardPolicy(weeklySpendCap: m('1000'))), m('1500'), []).first, 'weekly_cap_exceeded');
  });

  test('mirrors test_frozen_card_blocks_every_debit (purchase)', () {
    expect(purchaseViolations(card(status: 'frozen'), m('10'), []).first, 'card_frozen');
    expect(purchaseViolations(card(status: 'lost'), m('10'), []).first, 'card_lost');
  });

  group('offline balance rule (offline spend ceiling)', () {
    test('may go down to −ceiling, not further', () {
      expect(purchaseViolations(card(balance: '500', ceiling: '2000'), m('2500'), []), isEmpty);
      expect(purchaseViolations(card(balance: '500', ceiling: '2000'), m('2501'), []), ['insufficient_funds']);
    });
    test('a zero ceiling means the full balance is needed', () {
      expect(purchaseViolations(card(balance: '500', ceiling: '0'), m('501'), []), ['insufficient_funds']);
    });
  });

  group('allow-lists and merchants', () {
    test('category not on the allow-list', () {
      final p = CardPolicy(allowedCategoryIds: {meals});
      expect(purchaseViolations(card(policy: p), m('1000'), [line(chips, snacks, '1000')]), ['category_not_allowed']);
      expect(purchaseViolations(card(policy: p), m('3000'), [line(rice, meals, '3000')]), isEmpty);
    });
    test('custom-amount lines (no product/category) pass category rules, like the server', () {
      final p = CardPolicy(allowedCategoryIds: {meals}, blockedCategoryIds: {snacks});
      expect(purchaseViolations(card(policy: p), m('700'), [SaleLine(quantity: 1, unitPrice: m('700'))]), isEmpty);
    });
    test('blocked merchant / merchant not allowed', () {
      expect(purchaseViolations(card(policy: const CardPolicy(blockedMerchantIds: {7})), m('100'), [], merchantId: 7), ['merchant_blocked']);
      expect(purchaseViolations(card(policy: const CardPolicy(allowedMerchantIds: {8})), m('100'), [], merchantId: 7), ['merchant_blocked']);
      expect(purchaseViolations(card(policy: const CardPolicy(blockedMerchantIds: {7})), m('100'), []), isEmpty); // canteen
    });
  });

  test('every rule broken at once comes back in the backend order', () {
    final p = CardPolicy(
      perTransactionCap: m('100'),
      dailySpendCap: m('100'),
      weeklySpendCap: m('100'),
      blockedCategoryIds: {sugary},
      allowedCategoryIds: {meals},
      blockedProductIds: {soda},
      blockedMerchantIds: {5},
    );
    expect(
      purchaseViolations(card(status: 'frozen', balance: '0', ceiling: '0', policy: p), m('1500'), [line(soda, sugary, '1500')], merchantId: 5),
      [
        'card_frozen',
        'insufficient_funds',
        'per_transaction_cap_exceeded',
        'daily_cap_exceeded',
        'weekly_cap_exceeded',
        'category_blocked',
        'category_not_allowed',
        'item_blocked',
        'merchant_blocked',
      ],
    );
  });

  test('policy JSON from /pos/cache/ parses (null = no limit / no allow-list)', () {
    final p = CardPolicy.fromJson({
      'daily_spend_cap': '5000.00',
      'weekly_spend_cap': null,
      'per_transaction_cap': null,
      'p2p_daily_cap': null,
      'p2p_enabled': true,
      'low_balance_threshold': '2000.00',
      'blocked_category_ids': [2],
      'allowed_category_ids': null,
      'blocked_product_ids': [7],
      'blocked_merchant_ids': [],
      'allowed_merchant_ids': null,
    });
    expect(p.dailySpendCap, m('5000'));
    expect(p.weeklySpendCap, isNull);
    expect(p.allowedCategoryIds, isNull);
    expect(p.blockedProductIds, {7});
  });
}

import '../../core/money/money.dart';

/// The student's effective policy as shipped in /pos/cache/ (`card.policy`).
class CardPolicy {
  const CardPolicy({
    this.dailySpendCap,
    this.weeklySpendCap,
    this.perTransactionCap,
    this.p2pDailyCap,
    this.p2pEnabled = true,
    this.lowBalanceThreshold,
    this.blockedCategoryIds = const {},
    this.allowedCategoryIds,
    this.blockedProductIds = const {},
    this.blockedMerchantIds = const {},
    this.allowedMerchantIds,
  });

  final Money? dailySpendCap;
  final Money? weeklySpendCap;
  final Money? perTransactionCap;
  final Money? p2pDailyCap;
  final bool p2pEnabled;
  final Money? lowBalanceThreshold;
  final Set<int> blockedCategoryIds;
  final Set<int>? allowedCategoryIds; // null = no allow-list
  final Set<int> blockedProductIds;
  final Set<int> blockedMerchantIds;
  final Set<int>? allowedMerchantIds;

  static Set<int> _ids(Object? v) => {for (final x in (v as List? ?? const [])) (x as num).toInt()};

  factory CardPolicy.fromJson(Map<String, dynamic> j) => CardPolicy(
        dailySpendCap: Money.fromApi(j['daily_spend_cap']),
        weeklySpendCap: Money.fromApi(j['weekly_spend_cap']),
        perTransactionCap: Money.fromApi(j['per_transaction_cap']),
        p2pDailyCap: Money.fromApi(j['p2p_daily_cap']),
        p2pEnabled: j['p2p_enabled'] != false,
        lowBalanceThreshold: Money.fromApi(j['low_balance_threshold']),
        blockedCategoryIds: _ids(j['blocked_category_ids']),
        allowedCategoryIds: j['allowed_category_ids'] == null ? null : _ids(j['allowed_category_ids']),
        blockedProductIds: _ids(j['blocked_product_ids']),
        blockedMerchantIds: _ids(j['blocked_merchant_ids']),
        allowedMerchantIds: j['allowed_merchant_ids'] == null ? null : _ids(j['allowed_merchant_ids']),
      );
}

/// What the device knows about a card right now: the cached server numbers
/// already adjusted by this device's unsynced sales.
class CardState {
  const CardState({
    required this.status,
    required this.balance,
    required this.todaySpend,
    required this.weekSpend,
    required this.offlineSpendCeiling,
    required this.policy,
  });

  final String status; // active | frozen | lost
  final Money balance;
  final Money todaySpend;
  final Money weekSpend;
  final Money offlineSpendCeiling;
  final CardPolicy policy;
}

/// One cart line. [categoryId] is the PRODUCT's category when there is a
/// product (the server ignores a client-sent category for products).
class SaleLine {
  const SaleLine({this.productId, this.categoryId, required this.quantity, required this.unitPrice, this.description});
  final int? productId;
  final int? categoryId;
  final int quantity;
  final Money unitPrice;
  final String? description;
  Money get lineTotal => unitPrice * quantity;
}

/// Mirrors the backend's `wallets.services.debit_violations()` for a
/// PURCHASE, with the same reason codes in the same order:
///   card_frozen | card_lost, insufficient_funds, per_transaction_cap_exceeded,
///   daily_cap_exceeded, weekly_cap_exceeded, category_blocked,
///   category_not_allowed, item_blocked, merchant_blocked.
///
/// Offline, "insufficient funds" means going further below the cached
/// balance than the school's offline spend ceiling allows (API contract:
/// never let balance − offline spend go below −offline_spend_ceiling).
/// Pass [strictBalance] to require the full balance instead.
List<String> purchaseViolations(
  CardState card,
  Money amount,
  List<SaleLine> lines, {
  int? merchantId,
  bool strictBalance = false,
}) {
  final v = <String>[];
  if (card.status == 'frozen') {
    v.add('card_frozen');
  } else if (card.status == 'lost') {
    v.add('card_lost');
  }
  final floor = strictBalance ? const Money.zero() : -card.offlineSpendCeiling;
  if (card.balance - amount < floor) v.add('insufficient_funds');

  final p = card.policy;
  if (p.perTransactionCap != null && amount > p.perTransactionCap!) v.add('per_transaction_cap_exceeded');
  if (p.dailySpendCap != null && card.todaySpend + amount > p.dailySpendCap!) v.add('daily_cap_exceeded');
  if (p.weeklySpendCap != null && card.weekSpend + amount > p.weeklySpendCap!) v.add('weekly_cap_exceeded');

  final categoryIds = {for (final l in lines) if (l.categoryId != null) l.categoryId!};
  final productIds = {for (final l in lines) if (l.productId != null) l.productId!};
  if (categoryIds.intersection(p.blockedCategoryIds).isNotEmpty) v.add('category_blocked');
  if (p.allowedCategoryIds != null && categoryIds.difference(p.allowedCategoryIds!).isNotEmpty) {
    v.add('category_not_allowed');
  }
  if (productIds.intersection(p.blockedProductIds).isNotEmpty) v.add('item_blocked');
  if (merchantId != null &&
      (p.blockedMerchantIds.contains(merchantId) ||
          (p.allowedMerchantIds != null && !p.allowedMerchantIds!.contains(merchantId)))) {
    v.add('merchant_blocked');
  }
  return v;
}

/// All reason codes the device can show (for translations and tests).
const allReasonCodes = [
  'card_frozen',
  'card_lost',
  'insufficient_funds',
  'per_transaction_cap_exceeded',
  'daily_cap_exceeded',
  'weekly_cap_exceeded',
  'category_blocked',
  'category_not_allowed',
  'item_blocked',
  'merchant_blocked',
  'p2p_disabled',
  'p2p_cap_exceeded',
  'wallet_not_spendable',
  'pin_invalid',
  'unknown_card',
  'card_locked_on_device',
];

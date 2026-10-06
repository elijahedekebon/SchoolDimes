import 'package:schooldimes_pos/core/api/api_client.dart';

/// Scriptable stand-in for the backend's device endpoints.
class FakePosApi implements PosApi {
  Map<String, dynamic> cachePayload = {};
  Map<String, dynamic> rosterPayload = {'generated_at': '2026-10-05T07:00:00+00:00', 'cards': []};
  final List<List<Map<String, dynamic>>> syncCalls = [];
  final List<List<Map<String, dynamic>>> pinReportCalls = [];
  final List<Map<String, dynamic>> purchaseCalls = [];
  final List<List<Map<String, dynamic>>> tapCalls = [];
  final List<String?> cacheSinces = [];

  /// Applied server-side once, by idempotency key (like the real backend).
  final Map<String, Map<String, dynamic>> serverSales = {};
  final Set<String> serverTaps = {};
  ApiException? failNextSync, failNextPurchase, failNextTaps;
  bool purchaseTimesOutAfterServerApplies = false;
  Map<String, dynamic> Function(Map<String, dynamic> tx)? syncResult;
  ApiException Function(Map<String, dynamic>)? purchaseRefusal;

  @override
  Future<Map<String, dynamic>> device() async => {'id': 1};

  @override
  Future<Map<String, dynamic>> cache({String? since}) async {
    cacheSinces.add(since);
    return cachePayload;
  }

  @override
  Future<Map<String, dynamic>> roster({String? since}) async => rosterPayload;

  Map<String, dynamic> _record(Map<String, dynamic> tx) {
    final key = tx['idempotency_key'] as String;
    if (serverSales.containsKey(key)) return {...serverSales[key]!, 'status': 'duplicate'};
    final r = syncResult?.call(tx) ??
        {
          'idempotency_key': key,
          'status': 'applied',
          'transaction_id': serverSales.length + 1,
          'amount': tx['amount'],
          'applied_amount': tx['amount'],
          'shortfall_amount': '0.00',
          'flags': [],
          'reason': null,
        };
    serverSales[key] = r;
    return r;
  }

  @override
  Future<Map<String, dynamic>> sync(List<Map<String, dynamic>> transactions, List<Map<String, dynamic>> pinFailures) async {
    syncCalls.add(transactions);
    pinReportCalls.add(pinFailures);
    if (failNextSync != null) {
      final e = failNextSync!;
      failNextSync = null;
      throw e;
    }
    final results = [for (final t in transactions) _record(t)];
    return {
      'results': results,
      'balances': [
        for (final uid in {for (final t in transactions) t['card_uid']})
          {'card_uid': uid, 'card_status': 'active', 'wallet_id': 1, 'balance': '1000.00', 'today_spend': '0.00'}
      ],
      'server_time': '2026-10-05T07:00:00+00:00',
    };
  }

  @override
  Future<Map<String, dynamic>> purchase(Map<String, dynamic> sale) async {
    purchaseCalls.add(sale);
    if (purchaseRefusal != null) throw purchaseRefusal!(sale);
    if (failNextPurchase != null) {
      final e = failNextPurchase!;
      failNextPurchase = null;
      if (purchaseTimesOutAfterServerApplies) _record(sale);
      throw e;
    }
    final r = _record(sale);
    return {
      ...r,
      'balance': {'card_uid': sale['card_uid'], 'card_status': 'active', 'wallet_id': 1, 'balance': '7000.00', 'today_spend': '3000.00'}
    };
  }

  @override
  Future<Map<String, dynamic>> p2pTransfer(Map<String, dynamic> body) async => {'id': 1, ...body};

  @override
  Future<Map<String, dynamic>> attendanceTaps(List<Map<String, dynamic>> taps) async {
    tapCalls.add(taps);
    if (failNextTaps != null) {
      final e = failNextTaps!;
      failNextTaps = null;
      throw e;
    }
    return {
      'results': [
        for (final t in taps)
          {
            'idempotency_key': t['idempotency_key'],
            'status': serverTaps.add(t['idempotency_key'] as String) ? 'created' : 'duplicate',
            'record_id': 1,
            'reason': null,
          }
      ],
      'created': taps.length,
    };
  }
}

Map<String, dynamic> cachePayload({
  bool full = true,
  String generatedAt = '2026-10-05T07:00:00+00:00',
  List<Map<String, dynamic>>? cards,
  List<Map<String, dynamic>>? products,
}) =>
    {
      'generated_at': generatedAt,
      'full': full,
      'full_school_ids': full ? [1] : [],
      'spend_day': '2026-10-05',
      'week_start': '2026-10-05',
      'offline_spend_ceilings': {'1': '2000.00'},
      'pin_lockout_threshold': {'1': 3},
      'cards': cards ?? [card()],
      'products': products ??
          [
            {'id': 5, 'name': 'Rice & beans', 'category_id': 3, 'category_name': 'Meals', 'price': '3000.00', 'active': true, 'school_id': 1, 'merchant_id': null},
            {'id': 6, 'name': 'Soda', 'category_id': 2, 'category_name': 'Sugary drinks', 'price': '1500.00', 'active': true, 'school_id': 1, 'merchant_id': null},
          ],
      'categories': [
        {'id': 2, 'name': 'Sugary drinks', 'is_unhealthy': true, 'active': true, 'school_id': 1},
        {'id': 3, 'name': 'Meals', 'is_unhealthy': false, 'active': true, 'school_id': 1},
      ],
    };

/// PIN "5555" with 1 iteration (fast tests; same scheme as Django).
const fastPinHash = r'pbkdf2_sha256$1$fastSalt02$Om2sCKSzRV2SoeYCm9/Hi5ScUZE0Nk93jBvSoqrheVA=';

Map<String, dynamic> card({
  String uid = '04aabbcc',
  String status = 'active',
  String balance = '10000.00',
  String today = '0.00',
  String week = '0.00',
  Map<String, dynamic>? policy,
  String pinHash = fastPinHash,
}) =>
    {
      'card_id': 1,
      'card_uid': uid,
      'status': status,
      'pin_hash': pinHash,
      'student_id': 1,
      'student_display_name': 'Amina Nakato',
      'photo_url': null,
      'school_id': 1,
      'wallet_id': 1,
      'balance': balance,
      'today_spend': today,
      'week_spend': week,
      'offline_spend_ceiling': '2000.00',
      'policy': policy ??
          {
            'daily_spend_cap': '5000.00',
            'weekly_spend_cap': null,
            'per_transaction_cap': null,
            'p2p_daily_cap': null,
            'p2p_enabled': true,
            'low_balance_threshold': '2000.00',
            'blocked_category_ids': [2],
            'allowed_category_ids': null,
            'blocked_product_ids': [],
            'blocked_merchant_ids': [],
            'allowed_merchant_ids': null,
          },
    };

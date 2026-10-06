import 'package:schooldimes_parent/core/api/api_client.dart';
import 'package:schooldimes_parent/core/api/parent_api.dart';

/// In-memory parent backend for widget and unit tests.
class FakeParentApi implements ParentApi {
  bool loggedIn = false;
  String? wrongPasswordFor;
  ApiException? failNextDeposit;
  final List<String> depositKeys = [];
  int depositsCreated = 0;
  final Map<String, Json> _depositsByKey = {};
  final Map<int, Json> _deposits = {};
  List<String>? depositStatusSequence;
  String cardStatus = 'active';
  int freezeCalls = 0;
  final List<Json> raisedDisputes = [];
  String mainBalance = '25300.00';

  Json _student(int id, String name) => {
        'id': id,
        'name': name,
        'first_name': name.split(' ').first,
        'class_name': 'P4',
        'photo_url': null,
        'school': {'id': 1, 'name': 'Kampala Demo Primary School', 'branding': {}},
        'relationship': 'mother',
        'is_primary_contact': true,
        'main_wallet': {'id': id * 10, 'balance': id == 1 ? mainBalance : '8500.00'},
        'savings_wallet': {'id': id * 10 + 1, 'balance': '2000.00', 'withdrawal_window_start': null, 'withdrawal_window_end': null, 'withdrawal_window_open': false},
        'savings_goals': [
          {'id': 1, 'goal_name': 'New bicycle', 'target_amount': '50000.00', 'current_amount': '2000.00', 'progress_percent': 4.0, 'is_reached': false}
        ],
        'card': {'id': id, 'card_uid': '04aa', 'status': id == 1 ? cardStatus : 'active', 'updated_at': '2026-10-06T07:00:00Z'},
        'low_balance_threshold': '2000.00',
        'is_low_balance': false,
        'recent_transactions': [txn(id)],
      };

  Json txn(int studentId) => {
        'id': 100 + studentId,
        'wallet': studentId * 10,
        'wallet_type': 'main',
        'direction': 'debit',
        'amount': '3000.00',
        'entry_type': 'pos_purchase',
        'reference_id': 'pos:88',
        'description': 'Canteen till',
        'created_at': '2026-10-06T07:30:00Z',
        'pos': {
          'transaction_id': 88,
          'device_name': 'Canteen till',
          'merchant_id': null,
          'merchant_name': null,
          'sale_time': '2026-10-06T10:30:00+03:00',
          'sync_status': 'applied',
          'flags': [],
          'amount': '3000.00',
          'items': [
            {'product': 5, 'description': 'Rice & beans', 'category': 3, 'quantity': 1, 'unit_price': '3000.00', 'line_total': '3000.00'}
          ],
        },
        'dispute_target': {'pos_transaction': 88},
        'open_dispute': null,
      };

  @override
  Future<Json> login(String email, String password) async {
    if (email == wrongPasswordFor) throw ApiException(statusCode: 401, detail: 'No active account found with the given credentials');
    loggedIn = true;
    return {'access': 'a', 'refresh': 'r'};
  }

  @override
  Future<Json> register(Json body) async {
    loggedIn = true;
    return {'user': {'id': 9, 'email': body['email'], 'role': 'parent'}, 'access': 'a', 'refresh': 'r'};
  }

  @override
  Future<void> logout() async => loggedIn = false;
  @override
  Future<Json> me() async => {'id': 3, 'email': 'parent1@schooldimes.test', 'full_name': 'Moses Parent', 'role': 'parent', 'preferred_language': 'en', 'phone_number': '0772000111'};
  @override
  Future<Json> updateMe(Json body) async => {...await me(), ...body};
  @override
  Future<List<Json>> verifications() async => [];
  @override
  Future<Json> submitVerification(Json body) async => {...body, 'status': 'pending'};

  @override
  Future<Json> dashboard() async => {
        'user': await me(),
        'verification_status': 'verified',
        'unread_notifications': 2,
        'students': [_student(1, 'Amina Nakato'), _student(2, 'Brian Nakato')],
        'tip': {'id': 1, 'title': 'Needs vs. wants', 'body': 'Ask: do I need this?', 'language': 'en', 'target_age_range': ''},
      };

  @override
  Future<Json> transactions(int studentId, {Map<String, dynamic>? filters, int page = 1}) async =>
      {'count': 1, 'next': null, 'previous': null, 'results': [txn(studentId)]};
  @override
  Future<Json> spending(int studentId) async => {};
  @override
  Future<List<Json>> tips(String language) async => [];

  @override
  Future<Json> createDeposit(Json body) async {
    depositKeys.add(body['idempotency_key'] as String);
    if (failNextDeposit != null) {
      final e = failNextDeposit!;
      failNextDeposit = null;
      throw e;
    }
    return _depositsByKey.putIfAbsent(body['idempotency_key'] as String, () {
      depositsCreated++;
      final d = {
        'id': depositsCreated,
        'amount': body['amount'],
        'channel': body['channel'],
        'status': 'pending',
        'reference': 'SD-DEP-$depositsCreated',
        'instructions': {'type': 'momo_prompt', 'phone_number': '0772000111', 'message': 'Approve the payment on your phone.'},
        'failure_reason': '',
      };
      _deposits[depositsCreated] = d;
      return d;
    });
  }

  @override
  Future<Json> deposit(int id) async {
    if (depositStatusSequence != null && depositStatusSequence!.isNotEmpty) {
      final s = depositStatusSequence!.removeAt(0);
      if (s == 'network') throw ApiException(network: true);
      _deposits[id]!['status'] = s;
      if (s == 'confirmed') mainBalance = '30300.00';
    }
    return Map.of(_deposits[id]!);
  }

  @override
  Future<Json> deposits({Map<String, dynamic>? filters, int page = 1}) async =>
      {'count': _deposits.length, 'next': null, 'results': _deposits.values.toList()};
  @override
  Future<List<Json>> recurring() async => [];
  @override
  Future<Json> createRecurring(Json body) async => {'id': 1, ...body, 'next_run_at': '2026-10-12T05:00:00Z', 'last_status': '', 'consecutive_failures': 0};
  @override
  Future<Json> updateRecurring(int id, Json body) async => {'id': id, ...body};
  @override
  Future<void> deleteRecurring(int id) async {}
  @override
  Future<Json> createGift(Json body) async => {'id': 1, ...body, 'status': 'pending_payment', 'instructions': {'type': 'momo_prompt', 'message': 'Approve.'}};
  @override
  Future<List<Json>> gifts() async => [];
  @override
  Future<List<Json>> links() async => [];
  @override
  Future<Json> createLink(int studentId) async => {'id': 1, 'student': studentId, 'share_url': 'http://localhost:3000/give/tok', 'active': true};
  @override
  Future<Json> revokeLink(int id) async => {'id': id, 'active': false};
  @override
  Future<List<Json>> funds() async => [];
  @override
  Future<Json> fund(int id) async => {};
  @override
  Future<Json> contribute(int fundId, Json body) async => createDeposit(body);
  @override
  Future<Json> createFund(Json body) async => body;
  @override
  Future<Json> spendingControls(int studentId) async => {
        'student': studentId,
        'school_default': {'id': 1, 'daily_spend_cap': '6000.00', 'weekly_spend_cap': null, 'per_transaction_cap': '5000.00', 'p2p_daily_cap': '3000.00', 'p2p_enabled': true, 'blocked_categories': [], 'allowed_categories': [], 'blocked_items': [], 'blocked_merchants': [], 'allowed_merchants': []},
        'override': null,
        'effective': {'daily_spend_cap': '6000.00', 'p2p_enabled': true},
        'can_edit_override': true,
        'rule': 'parents_can_only_tighten',
      };
  @override
  Future<Json> createOverride(Json body) async => {'id': 4, ...body};
  @override
  Future<Json> updateOverride(int id, Json body) async => {'id': id, ...body};
  @override
  Future<List<Json>> categories() async => [];
  @override
  Future<List<Json>> products() async => [];
  @override
  Future<List<Json>> merchants() async => [];
  @override
  Future<Json> moveToSavings(int mainWalletId, String amount) async => {};
  @override
  Future<Json> moveFromSavings(int mainWalletId, String amount) async => {};
  @override
  Future<List<Json>> goals(int studentId) async => [];
  @override
  Future<Json> createGoal(Json body) async => body;
  @override
  Future<Json> updateGoal(int id, Json body) async => body;
  @override
  Future<void> deleteGoal(int id) async {}
  @override
  Future<Json> setWithdrawalWindow(int savingsWalletId, Json body) async => body;
  @override
  Future<Json> withdraw(int savingsWalletId, Json body) async => {'id': 1, 'status': 'pending', ...body};
  @override
  Future<List<Json>> payouts(int studentId) async => [];

  @override
  Future<Json> freezeCard(int cardId) async {
    freezeCalls++;
    cardStatus = 'frozen';
    return {'id': cardId, 'status': 'frozen'};
  }

  @override
  Future<Json> unfreezeCard(int cardId) async {
    cardStatus = 'active';
    return {'id': cardId, 'status': 'active'};
  }

  @override
  Future<Json> reportLost(int cardId) async {
    cardStatus = 'lost';
    return {'id': cardId, 'status': 'lost'};
  }

  @override
  Future<Json> p2pHistory(int studentId, {int page = 1}) async => {'count': 0, 'results': []};
  @override
  Future<Json> raiseDispute(Json body) async {
    raisedDisputes.add(body);
    return {'id': 4, ...body, 'status': 'open'};
  }

  @override
  Future<List<Json>> disputes() async => [];
  @override
  Future<Json> notifications({bool unreadOnly = false, int page = 1}) async => {'count': 0, 'unread_count': 0, 'results': []};
  @override
  Future<Json> markRead(int id) async => {};
  @override
  Future<Json> markAllRead() async => {'marked_read': 0};
  @override
  Future<Json> preferences() async => {'in_app_enabled': true, 'sms_enabled': false, 'push_enabled': true, 'low_balance_thresholds': {}};
  @override
  Future<Json> updatePreferences(Json body) async => body;
  @override
  Future<Json> registerPushToken(String token, String platform) async => {};
  @override
  Future<void> deletePushToken(String token) async {}
  @override
  Future<Json> myData() async => {};
  @override
  Future<String> myDataCsv() async => 'section,student\n';
  @override
  Future<List<Json>> dataRequests() async => [];
  @override
  Future<Json> createDataRequest(Json body) async => body;
}

/// Every call fails as if the phone had no data connection.
class FakeOfflineParentApi extends FakeParentApi {
  @override
  Future<Json> me() async => throw ApiException(network: true);
  @override
  Future<Json> dashboard() async => throw ApiException(network: true);
}

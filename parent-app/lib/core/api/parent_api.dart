import 'api_client.dart';

typedef Json = Map<String, dynamic>;

/// Every endpoint the parent app uses (docs/PARENT_APP_READINESS.md).
/// The app talks to this interface; tests substitute a fake.
abstract interface class ParentApi {
  // auth & profile
  Future<Json> login(String email, String password);
  Future<Json> register(Json body);
  Future<void> logout();
  Future<Json> me();
  Future<Json> updateMe(Json body);
  Future<List<Json>> verifications();
  Future<Json> submitVerification(Json body);
  // dashboard & history
  Future<Json> dashboard();
  Future<Json> transactions(int studentId, {Map<String, dynamic>? filters, int page = 1});
  Future<Json> spending(int studentId);
  Future<List<Json>> tips(String language);
  // top-ups
  Future<Json> createDeposit(Json body);
  Future<Json> deposit(int id);
  Future<Json> deposits({Map<String, dynamic>? filters, int page = 1});
  Future<List<Json>> recurring();
  Future<Json> createRecurring(Json body);
  Future<Json> updateRecurring(int id, Json body);
  Future<void> deleteRecurring(int id);
  // gifts & links
  Future<Json> createGift(Json body);
  Future<List<Json>> gifts();
  Future<List<Json>> links();
  Future<Json> createLink(int studentId);
  Future<Json> revokeLink(int id);
  // pooled funds
  Future<List<Json>> funds();
  Future<Json> fund(int id);
  Future<Json> contribute(int fundId, Json body);
  Future<Json> createFund(Json body);
  // spending controls
  Future<Json> spendingControls(int studentId);
  Future<Json> createOverride(Json body);
  Future<Json> updateOverride(int id, Json body);
  Future<List<Json>> categories();
  Future<List<Json>> products();
  Future<List<Json>> merchants();
  // savings
  Future<Json> moveToSavings(int mainWalletId, String amount);
  Future<Json> moveFromSavings(int mainWalletId, String amount);
  Future<List<Json>> goals(int studentId);
  Future<Json> createGoal(Json body);
  Future<Json> updateGoal(int id, Json body);
  Future<void> deleteGoal(int id);
  Future<Json> setWithdrawalWindow(int savingsWalletId, Json body);
  Future<Json> withdraw(int savingsWalletId, Json body);
  Future<List<Json>> payouts(int studentId);
  // cards & p2p
  Future<Json> freezeCard(int cardId);
  Future<Json> unfreezeCard(int cardId);
  Future<Json> reportLost(int cardId);
  Future<Json> p2pHistory(int studentId, {int page = 1});
  // disputes
  Future<Json> raiseDispute(Json body);
  Future<List<Json>> disputes();
  // notifications
  Future<Json> notifications({bool unreadOnly = false, int page = 1});
  Future<Json> markRead(int id);
  Future<Json> markAllRead();
  Future<Json> preferences();
  Future<Json> updatePreferences(Json body);
  Future<Json> registerPushToken(String token, String platform);
  Future<void> deletePushToken(String token);
  // privacy
  Future<Json> myData();
  Future<String> myDataCsv();
  Future<List<Json>> dataRequests();
  Future<Json> createDataRequest(Json body);
}

class HttpParentApi implements ParentApi {
  HttpParentApi(this.c);
  final ApiClient c;

  static Json _j(dynamic v) => (v as Map).cast<String, dynamic>();
  static List<Json> _results(dynamic v) =>
      ((v is Map ? v['results'] : v) as List).map((e) => (e as Map).cast<String, dynamic>()).toList();

  @override
  Future<Json> login(String email, String password) async {
    final r = _j(await c.post('/auth/login', {'email': email, 'password': password}, false));
    await c.tokens.save(r['access'] as String, r['refresh'] as String);
    return r;
  }

  @override
  Future<Json> register(Json body) async {
    final r = _j(await c.post('/auth/register', body, false));
    await c.tokens.save(r['access'] as String, r['refresh'] as String);
    return r;
  }

  @override
  Future<void> logout() async {
    final refresh = await c.tokens.refresh();
    try {
      if (refresh != null) await c.post('/auth/logout', {'refresh': refresh});
    } on ApiException {
      // signing out locally anyway
    }
    await c.tokens.clear();
  }

  @override
  Future<Json> me() async => _j(await c.get('/me'));
  @override
  Future<Json> updateMe(Json body) async => _j(await c.patch('/me', body));
  @override
  Future<List<Json>> verifications() async => _results(await c.get('/guardian-verifications/'));
  @override
  Future<Json> submitVerification(Json body) async => _j(await c.post('/guardian-verifications/', body));

  @override
  Future<Json> dashboard() async => _j(await c.get('/parent/dashboard/'));
  @override
  Future<Json> transactions(int studentId, {Map<String, dynamic>? filters, int page = 1}) async =>
      _j(await c.get('/students/$studentId/transactions/', query: {...?filters, 'page': page}));
  @override
  Future<Json> spending(int studentId) async => _j(await c.get('/analytics/students/$studentId/spending/'));
  @override
  Future<List<Json>> tips(String language) async => _results(await c.get('/financial-literacy-tips/', query: {'language': language}));

  @override
  Future<Json> createDeposit(Json body) async => _j(await c.post('/payments/deposits/', body));
  @override
  Future<Json> deposit(int id) async => _j(await c.get('/payments/deposits/$id/'));
  @override
  Future<Json> deposits({Map<String, dynamic>? filters, int page = 1}) async =>
      _j(await c.get('/payments/deposits/', query: {...?filters, 'page': page}));
  @override
  Future<List<Json>> recurring() async => _results(await c.get('/payments/recurring-topups/', query: {'page_size': 100}));
  @override
  Future<Json> createRecurring(Json body) async => _j(await c.post('/payments/recurring-topups/', body));
  @override
  Future<Json> updateRecurring(int id, Json body) async => _j(await c.patch('/payments/recurring-topups/$id/', body));
  @override
  Future<void> deleteRecurring(int id) async => c.delete('/payments/recurring-topups/$id/');

  @override
  Future<Json> createGift(Json body) async => _j(await c.post('/payments/gift-vouchers/', body));
  @override
  Future<List<Json>> gifts() async => _results(await c.get('/payments/gift-vouchers/', query: {'page_size': 100}));
  @override
  Future<List<Json>> links() async => _results(await c.get('/payments/topup-links/', query: {'page_size': 100}));
  @override
  Future<Json> createLink(int studentId) async => _j(await c.post('/payments/topup-links/', {'student': studentId}));
  @override
  Future<Json> revokeLink(int id) async => _j(await c.post('/payments/topup-links/$id/revoke/'));

  @override
  Future<List<Json>> funds() async => _results(await c.get('/pooled-funds/', query: {'page_size': 100}));
  @override
  Future<Json> fund(int id) async => _j(await c.get('/pooled-funds/$id/'));
  @override
  Future<Json> contribute(int fundId, Json body) async => _j(await c.post('/pooled-funds/$fundId/contribute/', body));
  @override
  Future<Json> createFund(Json body) async => _j(await c.post('/pooled-funds/', body));

  @override
  Future<Json> spendingControls(int studentId) async => _j(await c.get('/students/$studentId/spending-controls/'));
  @override
  Future<Json> createOverride(Json body) async => _j(await c.post('/policies/', body));
  @override
  Future<Json> updateOverride(int id, Json body) async => _j(await c.patch('/policies/$id/', body));
  @override
  Future<List<Json>> categories() async => _results(await c.get('/product-categories/', query: {'page_size': 100}));
  @override
  Future<List<Json>> products() async => _results(await c.get('/products/', query: {'page_size': 100}));
  @override
  Future<List<Json>> merchants() async => _results(await c.get('/merchants/', query: {'page_size': 100}));

  @override
  Future<Json> moveToSavings(int mainWalletId, String amount) async =>
      _j(await c.post('/wallets/$mainWalletId/savings/move-in/', {'amount': amount}));
  @override
  Future<Json> moveFromSavings(int mainWalletId, String amount) async =>
      _j(await c.post('/wallets/$mainWalletId/savings/move-out/', {'amount': amount}));
  @override
  Future<List<Json>> goals(int studentId) async => _results(await c.get('/savings-goals/', query: {'student': studentId}));
  @override
  Future<Json> createGoal(Json body) async => _j(await c.post('/savings-goals/', body));
  @override
  Future<Json> updateGoal(int id, Json body) async => _j(await c.patch('/savings-goals/$id/', body));
  @override
  Future<void> deleteGoal(int id) async => c.delete('/savings-goals/$id/');
  @override
  Future<Json> setWithdrawalWindow(int savingsWalletId, Json body) async =>
      _j(await c.put('/wallets/$savingsWalletId/savings/withdrawal-window/', body));
  @override
  Future<Json> withdraw(int savingsWalletId, Json body) async => _j(await c.post('/wallets/$savingsWalletId/savings/withdraw/', body));
  @override
  Future<List<Json>> payouts(int studentId) async => _results(await c.get('/payments/payouts/', query: {'student': studentId}));

  @override
  Future<Json> freezeCard(int cardId) async => _j(await c.post('/cards/$cardId/freeze/'));
  @override
  Future<Json> unfreezeCard(int cardId) async => _j(await c.post('/cards/$cardId/unfreeze/'));
  @override
  Future<Json> reportLost(int cardId) async => _j(await c.post('/cards/$cardId/report-lost/'));
  @override
  Future<Json> p2pHistory(int studentId, {int page = 1}) async => _j(await c.get('/students/$studentId/p2p-history/', query: {'page': page}));

  @override
  Future<Json> raiseDispute(Json body) async => _j(await c.post('/disputes/', body));
  @override
  Future<List<Json>> disputes() async => _results(await c.get('/disputes/', query: {'page_size': 100}));

  @override
  Future<Json> notifications({bool unreadOnly = false, int page = 1}) async =>
      _j(await c.get('/notifications/', query: {if (unreadOnly) 'unread': 'true', 'page': page}));
  @override
  Future<Json> markRead(int id) async => _j(await c.post('/notifications/$id/read/'));
  @override
  Future<Json> markAllRead() async => _j(await c.post('/notifications/read-all/'));
  @override
  Future<Json> preferences() async => _j(await c.get('/notifications/preferences/'));
  @override
  Future<Json> updatePreferences(Json body) async => _j(await c.patch('/notifications/preferences/', body));
  @override
  Future<Json> registerPushToken(String token, String platform) async =>
      _j(await c.post('/notifications/push-tokens/', {'token': token, 'platform': platform}));
  @override
  Future<void> deletePushToken(String token) async => c.delete('/notifications/push-tokens/${Uri.encodeComponent(token)}/');

  @override
  Future<Json> myData() async => _j(await c.get('/privacy/my-data/'));
  @override
  Future<String> myDataCsv() => c.getText('/privacy/my-data/', query: {'format': 'csv'});
  @override
  Future<List<Json>> dataRequests() async => _results(await c.get('/privacy/data-requests/', query: {'page_size': 100}));
  @override
  Future<Json> createDataRequest(Json body) async => _j(await c.post('/privacy/data-requests/', body));
}

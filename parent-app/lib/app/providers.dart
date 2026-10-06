import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import '../core/api/api_client.dart';
import '../core/api/parent_api.dart';
import '../core/storage/token_store.dart';
import '../features/dashboard/dashboard_cache.dart';

final tokenStoreProvider = Provider<TokenStore>((ref) => const SecureTokenStore());

/// Overridden in tests with a fake.
final parentApiProvider = Provider<ParentApi>((ref) {
  final client = ApiClient(tokens: ref.watch(tokenStoreProvider));
  client.onSignedOut = () => ref.read(authProvider.notifier).sessionEnded();
  return HttpParentApi(client);
});

class AuthState {
  const AuthState({this.me, this.sessionExpired = false});
  final Json? me;
  final bool sessionExpired;
  bool get signedIn => me != null;
  String get language => (me?['preferred_language'] as String?) ?? 'en';
}

class AuthNotifier extends AsyncNotifier<AuthState> {
  @override
  Future<AuthState> build() async {
    final hasToken = await ref.read(tokenStoreProvider).refresh() != null;
    if (!hasToken) return const AuthState();
    try {
      return AuthState(me: await ref.read(parentApiProvider).me());
    } on ApiException catch (e) {
      if (e.network) {
        // offline at start-up: stay signed in; screens show cached data
        return const AuthState(me: {'role': 'parent', 'offline': true});
      }
      return const AuthState();
    }
  }

  Future<void> login(String email, String password) async {
    final api = ref.read(parentApiProvider);
    await api.login(email.trim(), password);
    state = AsyncData(AuthState(me: await api.me()));
  }

  Future<void> register(Json body) async {
    final api = ref.read(parentApiProvider);
    await api.register(body);
    state = AsyncData(AuthState(me: await api.me()));
  }

  Future<void> logout() async {
    await ref.read(parentApiProvider).logout();
    await ref.read(dashboardCacheProvider).clear();
    state = const AsyncData(AuthState());
  }

  /// The refresh token was refused: back to sign-in with an explanation.
  void sessionEnded() => state = const AsyncData(AuthState(sessionExpired: true));

  Future<void> updateProfile(Json body) async {
    final me = await ref.read(parentApiProvider).updateMe(body);
    state = AsyncData(AuthState(me: me));
  }
}

final authProvider = AsyncNotifierProvider<AuthNotifier, AuthState>(AuthNotifier.new);

final dashboardCacheProvider = Provider<DashboardCache>((ref) => throw UnimplementedError('set in main()'));

Future<DashboardCache> createDashboardCache() async => DashboardCache(await getApplicationSupportDirectory());

class DashboardState {
  const DashboardState(this.data, {this.offlineSince});
  final Json data;

  /// Set when showing the cached copy because the network failed.
  final DateTime? offlineSince;
  List<Json> get students => (data['students'] as List).map((e) => (e as Map).cast<String, dynamic>()).toList();
  int get unread => (data['unread_notifications'] as int?) ?? 0;
  Json? get tip => (data['tip'] as Map?)?.cast<String, dynamic>();
  String? get verificationStatus => data['verification_status'] as String?;
}

class DashboardNotifier extends AsyncNotifier<DashboardState> {
  @override
  Future<DashboardState> build() => _load();

  Future<DashboardState> _load() async {
    final cache = ref.read(dashboardCacheProvider);
    try {
      final d = await ref.read(parentApiProvider).dashboard();
      await cache.save(d);
      return DashboardState(d);
    } on ApiException catch (e) {
      if (!e.network) rethrow;
      final cached = await cache.load();
      if (cached == null) rethrow;
      return DashboardState(cached.$1, offlineSince: cached.$2);
    }
  }

  Future<void> refresh() async {
    state = await AsyncValue.guard(_load);
  }
}

final dashboardProvider = AsyncNotifierProvider<DashboardNotifier, DashboardState>(DashboardNotifier.new);

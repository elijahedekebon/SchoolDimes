import 'dart:io';

import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:path_provider/path_provider.dart';

import '../core/api/api_client.dart';
import '../core/config/env.dart';
import '../core/db/database.dart';
import '../core/security/secure_store.dart';
import '../features/provisioning/device_config.dart';
import '../features/provisioning/provisioning_service.dart';

/// Everything a provisioned device needs, created once per provisioning.
class Session {
  Session({required this.config, required this.db, required this.api, required this.revoked});
  final DeviceConfig? config;
  final AppDatabase db;
  final ApiClient? api;
  final bool revoked;

  bool get provisioned => config != null;
}

final secretStoreProvider = Provider<SecretStore>((ref) => const PlatformSecretStore());

final provisioningProvider = Provider<ProvisioningService>((ref) => ProvisioningService(
      ref.watch(secretStoreProvider),
      (url, token) => ApiClient(baseUrl: url, token: token),
      requireHttps: !Env.isDev,
    ));

/// Opens the encrypted database once per app run.
final databaseProvider = FutureProvider<AppDatabase>((ref) async {
  final key = await ref.watch(provisioningProvider).databaseKey();
  final dir = await getApplicationSupportDirectory();
  final db = AppDatabase(openEncrypted(File('${dir.path}/schooldimes_pos.db'), key));
  ref.onDispose(db.close);
  return db;
});

class SessionNotifier extends AsyncNotifier<Session> {
  @override
  Future<Session> build() async {
    final db = await ref.watch(databaseProvider.future);
    final prov = ref.watch(provisioningProvider);
    final config = await prov.load();
    final lang = await db.getKv('language') ?? config?.defaultLanguage;
    return Session(
      config: config,
      db: db,
      api: config == null ? null : ApiClient(baseUrl: config.baseUrl, token: config.token, language: lang),
      revoked: await prov.isRevoked(),
    );
  }

  Future<void> provision({required String baseUrl, required String token, required String adminPin}) async {
    final db = await ref.read(databaseProvider.future);
    await ref.read(provisioningProvider).provision(baseUrl: baseUrl, token: token, adminPin: adminPin, db: db);
    ref.invalidateSelf();
    await future;
  }

  /// The server answered "Invalid or revoked device token.": stop transacting.
  Future<void> markRevoked() async {
    await ref.read(provisioningProvider).markRevoked();
    final s = state.value;
    if (s != null) state = AsyncData(Session(config: s.config, db: s.db, api: s.api, revoked: true));
  }

  /// Device info refreshed from GET /pos/device/ (settings may change).
  Future<void> updateInfo(Map<String, dynamic> info) async {
    final s = state.value;
    if (s?.config == null) return;
    final cfg = s!.config!.copyWith(info: info);
    await ref.read(provisioningProvider).saveInfo(cfg);
    state = AsyncData(Session(config: cfg, db: s.db, api: s.api, revoked: s.revoked));
  }

  Future<void> setLanguage(String lang) async {
    final s = state.value;
    if (s == null) return;
    await s.db.setKv('language', lang);
    s.api?.language = lang;
    ref.invalidate(localeProvider);
  }
}

final sessionProvider = AsyncNotifierProvider<SessionNotifier, Session>(SessionNotifier.new);

/// The UI language: staff choice, else the school's default language.
final localeProvider = FutureProvider<String>((ref) async {
  final s = await ref.watch(sessionProvider.future);
  return await s.db.getKv('language') ?? s.config?.defaultLanguage ?? 'en';
});

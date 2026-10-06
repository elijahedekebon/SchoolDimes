import 'dart:convert';

import 'package:drift/drift.dart';

import '../../core/api/api_client.dart';
import '../../core/db/database.dart';
import '../../core/security/secure_store.dart';
import 'device_config.dart';

typedef ApiFactory = PosApi Function(String baseUrl, String token);

class ProvisioningError implements Exception {
  ProvisioningError(this.code, [this.detail]);
  final String code; // invalid_token | unreachable | unsynced_other_device | https_required
  final String? detail;
  @override
  String toString() => 'ProvisioningError($code, $detail)';
}

/// Stores the device identity in secure storage. Keys:
///   device_config — DeviceConfig JSON (token included)
///   db_key        — the local database encryption key
///   revoked       — "1" once the server said the token is invalid/revoked
class ProvisioningService {
  ProvisioningService(this.store, this.apiFactory, {this.requireHttps = false});

  final SecretStore store;
  final ApiFactory apiFactory;
  final bool requireHttps;

  Future<DeviceConfig?> load() async {
    final raw = await store.read('device_config');
    return raw == null ? null : DeviceConfig.fromJson((jsonDecode(raw) as Map).cast<String, dynamic>());
  }

  Future<bool> isRevoked() async => (await store.read('revoked')) == '1';
  Future<void> markRevoked() => store.write('revoked', '1');

  Future<String> databaseKey() async {
    var key = await store.read('db_key');
    if (key == null) {
      key = randomHex(32);
      await store.write('db_key', key);
    }
    return key;
  }

  /// Validates [token] with GET /pos/device/ and stores the identity.
  /// Unsynced records are never deleted: switching to a DIFFERENT device id
  /// is refused while any exist (rotating this device's token is fine).
  Future<DeviceConfig> provision({
    required String baseUrl,
    required String token,
    required String adminPin,
    required AppDatabase db,
  }) async {
    final url = baseUrl.trim().replaceAll(RegExp(r'/+$'), '');
    if (requireHttps && !url.startsWith('https://')) throw ProvisioningError('https_required');
    final Map<String, dynamic> info;
    try {
      info = await apiFactory(url, token.trim()).device();
    } on ApiException catch (e) {
      if (e.revoked) throw ProvisioningError('invalid_token', e.detail);
      if (e.unreachable) throw ProvisioningError('unreachable', e.detail);
      throw ProvisioningError(e.code ?? 'error', e.detail);
    }
    final previous = await load();
    if (previous != null && previous.deviceId != info['id']) {
      if (await unsyncedCount(db) > 0) throw ProvisioningError('unsynced_other_device');
      await db.wipeCache();
      await db.setKv('cache_generated_at', null);
      await db.setKv('roster_generated_at', null);
    }
    final config = DeviceConfig(
      baseUrl: url,
      token: token.trim(),
      info: info,
      adminPinHash: adminPin.isEmpty && previous != null ? previous.adminPinHash : hashAdminPin(adminPin),
    );
    await store.write('device_config', config.encode());
    await store.write('revoked', null);
    return config;
  }

  Future<void> saveInfo(DeviceConfig config) => store.write('device_config', config.encode());

  static Future<int> unsyncedCount(AppDatabase db) async {
    final sales = await (db.selectOnly(db.saleQueue)
          ..addColumns([db.saleQueue.id.count()])
          ..where(db.saleQueue.status.equals('pending')))
        .map((r) => r.read(db.saleQueue.id.count()) ?? 0)
        .getSingle();
    final taps = await (db.selectOnly(db.attendanceQueue)
          ..addColumns([db.attendanceQueue.id.count()])
          ..where(db.attendanceQueue.status.equals('pending')))
        .map((r) => r.read(db.attendanceQueue.id.count()) ?? 0)
        .getSingle();
    return sales + taps;
  }
}

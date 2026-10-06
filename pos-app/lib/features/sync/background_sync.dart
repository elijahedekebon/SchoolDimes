import 'dart:convert';
import 'dart:io';

import 'package:flutter/widgets.dart';
import 'package:path_provider/path_provider.dart';
import 'package:workmanager/workmanager.dart';

import '../../core/api/api_client.dart';
import '../../core/db/database.dart';
import '../../core/security/secure_store.dart';
import '../provisioning/device_config.dart';
import 'sync_engine.dart';

const backgroundSyncTask = 'schooldimes.pos.sync';

/// Android background sync via WorkManager (every ~15 min, when a network
/// is available). Runs in its own isolate: it opens the encrypted database
/// and the device token itself. Pending records are never deleted.
@pragma('vm:entry-point')
void backgroundDispatcher() {
  Workmanager().executeTask((task, _) async {
    WidgetsFlutterBinding.ensureInitialized();
    const store = PlatformSecretStore();
    final raw = await store.read('device_config');
    final key = await store.read('db_key');
    if (raw == null || key == null || await store.read('revoked') == '1') return true;
    final cfg = DeviceConfig.fromJson((jsonDecode(raw) as Map).cast<String, dynamic>());
    final dir = await getApplicationSupportDirectory();
    final db = AppDatabase(openEncrypted(File('${dir.path}/schooldimes_pos.db'), key));
    try {
      final report = await SyncEngine(
        db: db,
        api: ApiClient(baseUrl: cfg.baseUrl, token: cfg.token),
        canSell: cfg.canSell,
        canRecordAttendance: cfg.canRecordAttendance,
        onRevoked: () => store.write('revoked', '1'),
      ).run(manual: true);
      return !report.networkFailed;
    } finally {
      await db.close();
    }
  });
}

Future<void> registerBackgroundSync() async {
  if (!Platform.isAndroid) return;
  await Workmanager().initialize(backgroundDispatcher);
  await Workmanager().registerPeriodicTask(
    backgroundSyncTask,
    backgroundSyncTask,
    frequency: const Duration(minutes: 15),
    constraints: Constraints(networkType: NetworkType.connected),
    existingWorkPolicy: ExistingPeriodicWorkPolicy.keep,
  );
}

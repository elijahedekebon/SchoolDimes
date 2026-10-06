import 'dart:async';

import 'package:connectivity_plus/connectivity_plus.dart';
import 'package:drift/drift.dart';
import 'package:flutter/foundation.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/api/api_client.dart';
import '../core/config/env.dart';
import '../core/nfc/nfc_reader.dart';
import '../core/security/pin_verifier.dart';
import '../features/attendance/attendance_service.dart';
import '../features/cache/cache_service.dart';
import '../features/sale/sale_service.dart';
import '../features/sync/sync_engine.dart';
import 'session.dart';

Session _session(Ref ref) => ref.watch(sessionProvider).requireValue;

final nfcReaderProvider = Provider<NfcReader>((ref) => NfcReader());

final saleServiceProvider = Provider<SaleService>((ref) {
  final s = _session(ref);
  return SaleService(db: s.db, api: s.api!, verifier: PinVerifier(), merchantId: s.config!.merchantId);
});

final attendanceServiceProvider = Provider<AttendanceService>((ref) => AttendanceService(_session(ref).db));

final cacheServiceProvider = Provider<CacheService>((ref) {
  final s = _session(ref);
  return CacheService(s.db, s.api!);
});

final syncEngineProvider = Provider<SyncEngine>((ref) {
  final s = _session(ref);
  return SyncEngine(
    db: s.db,
    api: s.api!,
    canSell: s.config!.canSell,
    canRecordAttendance: s.config!.canRecordAttendance,
    onRevoked: () => ref.read(sessionProvider.notifier).markRevoked(),
  );
});

/// Connectivity as reported by the OS (online != reachable; a failed call
/// still falls back to the offline queue).
final connectivityProvider = StreamProvider<bool>((ref) async* {
  final c = Connectivity();
  bool up(List<ConnectivityResult> r) => r.any((x) => x != ConnectivityResult.none);
  yield up(await c.checkConnectivity());
  yield* c.onConnectivityChanged.map(up);
});

/// Status shown on every screen.
class PosStatus {
  PosStatus({required this.online, required this.pending, this.lastSync, this.cacheRefreshedAt, this.syncing = false});
  final bool online;
  final int pending;
  final DateTime? lastSync;
  final DateTime? cacheRefreshedAt;
  final bool syncing;
  bool get cacheStale => cacheRefreshedAt == null || DateTime.now().difference(cacheRefreshedAt!) > Env.cacheStaleAfter;
}

final syncingProvider = NotifierProvider<SyncingFlag, bool>(SyncingFlag.new);

class SyncingFlag extends Notifier<bool> {
  @override
  bool build() => false;
  void set(bool v) => state = v;
}

final statusProvider = StreamProvider<PosStatus>((ref) async* {
  final s = _session(ref);
  final online = ref.watch(connectivityProvider).value ?? false;
  final syncing = ref.watch(syncingProvider);
  while (true) {
    try {
      final pendingSales =
          await (s.db.selectOnly(s.db.saleQueue)
                ..addColumns([s.db.saleQueue.id.count()])
                ..where(s.db.saleQueue.status.equals('pending')))
              .map((r) => r.read(s.db.saleQueue.id.count()) ?? 0)
              .getSingle();
      final pendingTaps =
          await (s.db.selectOnly(s.db.attendanceQueue)
                ..addColumns([s.db.attendanceQueue.id.count()])
                ..where(s.db.attendanceQueue.status.equals('pending')))
              .map((r) => r.read(s.db.attendanceQueue.id.count()) ?? 0)
              .getSingle();
      final last = await s.db.getKv('last_sync_ok_at');
      final cache = await s.db.getKv('cache_refreshed_at');
      yield PosStatus(
        online: online,
        pending: pendingSales + pendingTaps,
        lastSync: last == null ? null : DateTime.parse(last),
        cacheRefreshedAt: cache == null ? null : DateTime.parse(cache),
        syncing: syncing,
      );
    } on StateError {
      return; // database closed (app shutting down / re-provisioned)
    }
    await Future<void>.delayed(const Duration(seconds: 3));
  }
});

/// Triggers: connectivity regained, a periodic timer while the app is open,
/// and "Sync now". (Background work: see background_sync.dart.)
final syncControllerProvider = Provider<SyncController>((ref) {
  final c = SyncController(ref);
  ref.onDispose(c.dispose);
  return c;
});

class SyncController {
  SyncController(this.ref) {
    _timer = Timer.periodic(Env.syncInterval, (_) {
      debugPrint('sync trigger: timer');
      run();
    });
    ref.listen<AsyncValue<bool>>(connectivityProvider, (prev, next) {
      if (next.value == true && prev?.value != true) run();
    });
    Future.microtask(run);
  }

  final Ref ref;
  late final Timer _timer;
  Timer? _nudge;

  /// A new record was queued: sync soon (debounced) instead of waiting for
  /// the timer. Offline, the attempt just fails fast and backs off.
  void nudge() {
    _nudge?.cancel();
    _nudge = Timer(const Duration(seconds: 3), () {
      debugPrint('sync trigger: nudge');
      run();
    });
  }

  Future<SyncReport> run({bool manual = false}) async {
    final session = ref.read(sessionProvider).value;
    if (session == null || !session.provisioned || session.revoked) return SyncReport();
    ref.read(syncingProvider.notifier).set(true);
    try {
      final report = await ref.read(syncEngineProvider).run(manual: manual);
      if (!report.networkFailed && !report.revoked) await _refreshDeviceInfo(session.api!);
      return report;
    } finally {
      ref.read(syncingProvider.notifier).set(false);
    }
  }

  Future<void> _refreshDeviceInfo(ApiClient api) async {
    try {
      await ref.read(sessionProvider.notifier).updateInfo(await api.device());
    } on ApiException {
      // next run
    }
  }

  void dispose() {
    _timer.cancel();
    _nudge?.cancel();
  }
}

import 'dart:async';
import 'dart:convert' show jsonDecode;
import 'dart:math';

import 'package:drift/drift.dart';

import '../../core/api/api_client.dart';
import '../../core/config/env.dart';
import '../../core/db/database.dart';
import '../../core/money/money.dart';
import '../cache/cache_service.dart';
import '../sale/pin_guard.dart';

class SyncReport {
  int salesSent = 0, applied = 0, duplicates = 0, shortfalls = 0, rejected = 0;
  int tapsSent = 0, tapsCreated = 0, tapsRejected = 0;
  bool networkFailed = false, revoked = false, cacheRefreshed = false;
  String? error;
  @override
  String toString() =>
      'sales $salesSent (applied $applied, dup $duplicates, shortfall $shortfalls, rejected $rejected), taps $tapsSent, '
      'network ${networkFailed ? 'FAILED' : 'ok'}${revoked ? ', REVOKED' : ''}';
}

/// Pushes the write-ahead queues, oldest first, in batches; handles every
/// documented per-item result; never deletes an unsynced record.
class SyncEngine {
  SyncEngine({
    required this.db,
    required this.api,
    required this.canSell,
    required this.canRecordAttendance,
    this.batchSize = Env.syncBatchSize,
    this.retention = Env.syncedRetention,
    this.onRevoked,
    Random? random,
  })  : cache = CacheService(db, api),
        pins = PinGuard(db),
        _random = random ?? Random();

  final AppDatabase db;
  final PosApi api;
  final bool canSell;
  final bool canRecordAttendance;
  final int batchSize;
  final Duration retention;
  final Future<void> Function()? onRevoked;
  final CacheService cache;
  final PinGuard pins;
  final Random _random;

  int _failures = 0;
  DateTime? _nextAllowed;
  Completer<SyncReport>? _running;

  /// Exponential backoff with jitter after network failures (5 s … 10 min).
  Duration backoffFor(int failures) {
    final base = Duration(seconds: min(600, 5 * pow(2, max(0, failures - 1)).toInt()));
    final jitter = 0.5 + _random.nextDouble(); // 0.5x .. 1.5x
    return Duration(milliseconds: (base.inMilliseconds * jitter).round());
  }

  bool get backingOff => _nextAllowed != null && DateTime.now().isBefore(_nextAllowed!);

  /// [manual] ("Sync now") ignores the backoff. Concurrent calls share one run.
  Future<SyncReport> run({bool manual = false, bool refreshCache = true}) {
    if (_running != null) return _running!.future;
    if (!manual && backingOff) return Future.value(SyncReport()..error = 'backoff');
    final c = _running = Completer<SyncReport>();
    _run(refreshCache).then(c.complete, onError: c.completeError).whenComplete(() => _running = null);
    return c.future;
  }

  Future<SyncReport> _run(bool refreshCache) async {
    final report = SyncReport();
    try {
      if (canSell) await _pushSales(report);
      if (canRecordAttendance) await _pushTaps(report);
      if (refreshCache) {
        if (canSell) await cache.refresh();
        if (canRecordAttendance) await cache.refreshRoster();
        report.cacheRefreshed = true;
      }
      await _prune();
      _failures = 0;
      _nextAllowed = null;
      await db.setKv('last_sync_ok_at', DateTime.now().toUtc().toIso8601String());
      await db.log('sync', true, report.toString());
    } on ApiException catch (e) {
      if (e.revoked) {
        report.revoked = true;
        await onRevoked?.call();
      } else {
        report.networkFailed = e.unreachable;
        report.error = e.toString();
        _failures++;
        _nextAllowed = DateTime.now().add(backoffFor(_failures));
      }
      await db.log('sync', false, '${report.error ?? 'revoked'} :: $report');
    }
    return report;
  }

  Future<void> _pushSales(SyncReport report) async {
    var pinReports = await pins.pendingReports();
    while (true) {
      final batch = await (db.select(db.saleQueue)
            ..where((t) => t.status.equals('pending'))
            ..orderBy([(t) => OrderingTerm.asc(t.createdAt), (t) => OrderingTerm.asc(t.id)])
            ..limit(batchSize))
          .get();
      if (batch.isEmpty && pinReports.isEmpty) return;
      final txs = [
        for (final s in batch)
          {
            'idempotency_key': s.idempotencyKey,
            'card_uid': s.cardUid,
            'amount': Money(s.amountCents).toApi(),
            'items': _decode(s.itemsJson),
            'device_local_timestamp': s.deviceLocalTimestamp,
            'pin_verified': true,
          }
      ];
      // attempts are counted before sending; a network failure leaves every row pending
      for (final s in batch) {
        await (db.update(db.saleQueue)..where((t) => t.id.equals(s.id))).write(SaleQueueCompanion(attempts: Value(s.attempts + 1)));
      }
      final resp = await api.sync(txs, pinReports);
      await pins.markReported(pinReports);
      pinReports = const [];
      report.salesSent += batch.length;
      final byKey = {for (final r in (resp['results'] as List).cast<Map>()) r['idempotency_key']: r};
      final now = DateTime.now().toUtc();
      await db.transaction(() async {
        for (final s in batch) {
          final r = byKey[s.idempotencyKey];
          if (r == null) continue; // no answer for it: stays pending
          final status = r['status'] as String;
          switch (status) {
            case 'applied':
              report.applied++;
            case 'duplicate':
              report.duplicates++;
            case 'shortfall':
              report.shortfalls++;
            case 'rejected':
              report.rejected++;
          }
          await (db.update(db.saleQueue)..where((t) => t.id.equals(s.id))).write(SaleQueueCompanion(
            status: Value(status),
            appliedCents: Value(r['applied_amount'] == null ? null : Money.parse(r['applied_amount'] as String).cents),
            shortfallCents: Value(r['shortfall_amount'] == null ? null : Money.parse(r['shortfall_amount'] as String).cents),
            flags: Value(((r['flags'] as List?) ?? const []).join(',')),
            reason: Value(r['reason'] as String?),
            serverTransactionId: Value(r['transaction_id'] as int?),
            syncedAt: Value(now),
          ));
        }
      });
      await cache.applyBalances((resp['balances'] as List).cast<Map>());
      if (batch.length < batchSize) return;
    }
  }

  Future<void> _pushTaps(SyncReport report) async {
    while (true) {
      final batch = await (db.select(db.attendanceQueue)
            ..where((t) => t.status.equals('pending'))
            ..orderBy([(t) => OrderingTerm.asc(t.createdAt), (t) => OrderingTerm.asc(t.id)])
            ..limit(batchSize))
          .get();
      if (batch.isEmpty) return;
      final resp = await api.attendanceTaps([
        for (final t in batch)
          {
            'idempotency_key': t.idempotencyKey,
            'card_uid': t.cardUid,
            'direction': t.direction,
            'device_local_timestamp': t.deviceLocalTimestamp,
          }
      ]);
      report.tapsSent += batch.length;
      final byKey = {for (final r in (resp['results'] as List).cast<Map>()) r['idempotency_key']: r};
      final now = DateTime.now().toUtc();
      for (final t in batch) {
        final r = byKey[t.idempotencyKey];
        if (r == null) continue;
        final status = r['status'] as String;
        if (status == 'created') report.tapsCreated++;
        if (status == 'rejected') report.tapsRejected++;
        await (db.update(db.attendanceQueue)..where((x) => x.id.equals(t.id))).write(AttendanceQueueCompanion(
          status: Value(status),
          reason: Value(r['reason'] as String?),
          attempts: Value(t.attempts + 1),
          syncedAt: Value(now),
        ));
      }
      if (batch.length < batchSize) return;
    }
  }

  /// Synced rows are pruned only after the retention period; pending rows never.
  Future<void> _prune() async {
    final cutoff = DateTime.now().toUtc().subtract(retention);
    await (db.delete(db.saleQueue)..where((t) => t.status.isNotIn(['pending']) & t.syncedAt.isSmallerThanValue(cutoff))).go();
    await (db.delete(db.attendanceQueue)..where((t) => t.status.isNotIn(['pending']) & t.syncedAt.isSmallerThanValue(cutoff))).go();
    await (db.delete(db.syncLog)..where((t) => t.at.isSmallerThanValue(cutoff))).go();
  }

  static Object? _decode(String json) => json.isEmpty ? const [] : jsonDecode(json);
}


import 'package:drift/drift.dart';

import '../../core/db/database.dart';
import '../../core/time/kampala.dart';

/// Wrong-PIN counting on this device. After `pin_lockout_threshold` wrong
/// PINs a card is refused here; every failure is reported on the next sync
/// (`pin_failures`), and the server freezes the card when the threshold is
/// reached across devices (API contract, Section D).
class PinGuard {
  PinGuard(this.db);
  final AppDatabase db;

  Future<PinFailure?> _row(String uid) => (db.select(db.pinFailures)..where((t) => t.cardUid.equals(uid))).getSingleOrNull();

  Future<bool> isLocked(String uid) async => (await _row(uid))?.locked ?? false;

  /// Returns how many tries are left (0 = now locked).
  Future<int> recordFailure(String uid, int threshold, {DateTime? now}) async {
    final at = (now ?? DateTime.now()).toUtc();
    final row = await _row(uid);
    final failures = (row?.failures ?? 0) + 1;
    final locked = failures >= threshold;
    await db.into(db.pinFailures).insertOnConflictUpdate(PinFailuresCompanion.insert(
          cardUid: uid,
          failures: failures,
          unreported: (row?.unreported ?? 0) + 1,
          firstFailureAt: row?.firstFailureAt ?? at,
          lastFailureAt: at,
          locked: Value(locked),
        ));
    return locked ? 0 : threshold - failures;
  }

  /// A correct PIN resets the local counter (failures already counted stay
  /// queued for reporting).
  Future<void> recordSuccess(String uid) async {
    final row = await _row(uid);
    if (row == null) return;
    if (row.unreported == 0) {
      await (db.delete(db.pinFailures)..where((t) => t.cardUid.equals(uid))).go();
    } else {
      await (db.update(db.pinFailures)..where((t) => t.cardUid.equals(uid)))
          .write(const PinFailuresCompanion(failures: Value(0), locked: Value(false)));
    }
  }

  /// Admin unlock from the staff settings, or the PIN was reset centrally.
  Future<void> unlock(String uid) => (db.update(db.pinFailures)..where((t) => t.cardUid.equals(uid)))
      .write(const PinFailuresCompanion(failures: Value(0), locked: Value(false)));

  Future<List<Map<String, dynamic>>> pendingReports() async {
    final rows = await (db.select(db.pinFailures)..where((t) => t.unreported.isBiggerThanValue(0))).get();
    return [
      for (final r in rows)
        {'card_uid': r.cardUid, 'failed_attempts': r.unreported, 'device_local_timestamp': Kampala.isoLocal(r.lastFailureAt)}
    ];
  }

  Future<void> markReported(List<Map<String, dynamic>> reports) async {
    for (final r in reports) {
      final row = await _row(r['card_uid'] as String);
      if (row == null) continue;
      final left = row.unreported - (r['failed_attempts'] as int);
      await (db.update(db.pinFailures)..where((t) => t.cardUid.equals(row.cardUid)))
          .write(PinFailuresCompanion(unreported: Value(left < 0 ? 0 : left)));
    }
  }
}

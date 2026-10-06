import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../core/config/env.dart';
import '../../core/db/database.dart';
import '../../core/time/kampala.dart';

enum TapStatus { recorded, duplicateIgnored, unknownCard, lostCard }

class TapResult {
  TapResult(this.status, {this.card});
  final TapStatus status;
  final RosterCard? card;
}

/// Gate taps: no PIN, no money. Each tap is written to the local queue first
/// and synced in batches to POST /attendance/tap/.
class AttendanceService {
  AttendanceService(this.db, {Uuid? uuid, this.dedupWindow = Env.attendanceDedupWindow}) : _uuid = uuid ?? const Uuid();

  final AppDatabase db;
  final Uuid _uuid;
  final Duration dedupWindow;

  Future<TapResult> tap(String uid, String direction, {DateTime? now}) async {
    final at = (now ?? DateTime.now()).toUtc();
    final card = await (db.select(db.rosterCards)..where((t) => t.cardUid.equals(uid))).getSingleOrNull();
    if (card == null) return TapResult(TapStatus.unknownCard);
    if (card.status == 'lost') return TapResult(TapStatus.lostCard, card: card);
    final recent = await (db.select(db.attendanceQueue)
          ..where((t) => t.cardUid.equals(uid) & t.direction.equals(direction) & t.createdAt.isBiggerThanValue(at.subtract(dedupWindow)))
          ..limit(1))
        .getSingleOrNull();
    if (recent != null) return TapResult(TapStatus.duplicateIgnored, card: card);
    await db.into(db.attendanceQueue).insert(AttendanceQueueCompanion.insert(
          idempotencyKey: _uuid.v4(),
          cardUid: uid,
          studentName: card.displayName,
          direction: direction,
          deviceLocalTimestamp: Kampala.isoLocal(at),
          kampalaDay: Kampala.day(at),
          createdAt: at,
          status: 'pending',
        ));
    return TapResult(TapStatus.recorded, card: card);
  }
}

import 'dart:convert';

import 'package:drift/drift.dart';

import '../../core/db/database.dart';
import '../../core/money/money.dart';
import '../../core/time/kampala.dart';
import '../policy/policy_engine.dart';

/// Turns the cached server numbers into "what the card looks like now":
/// balance minus this device's unsynced sales, today's / this week's spend
/// plus them (and zero if the cached day/week is over).
class CardRepository {
  CardRepository(this.db);
  final AppDatabase db;

  Future<CachedCard?> find(String uid) => (db.select(db.cachedCards)..where((t) => t.cardUid.equals(uid))).getSingleOrNull();

  Future<CardState> stateOf(CachedCard c, {DateTime? now}) async {
    final t = now ?? DateTime.now();
    final today = Kampala.day(t), week = Kampala.weekStart(t);
    final pending = await (db.select(db.saleQueue)
          ..where((s) => s.cardUid.equals(c.cardUid) & s.status.equals('pending')))
        .get();
    final pendingTotal = Money.sum(pending.map((s) => Money(s.amountCents)));
    final pendingToday = Money.sum(pending.where((s) => s.kampalaDay == today).map((s) => Money(s.amountCents)));
    final pendingWeek = Money.sum(pending.where((s) => s.kampalaWeek == week).map((s) => Money(s.amountCents)));
    return CardState(
      status: c.status,
      balance: Money(c.balanceCents) - pendingTotal,
      todaySpend: (c.spendDay == today ? Money(c.todaySpendCents) : const Money.zero()) + pendingToday,
      weekSpend: (c.weekStart == week ? Money(c.weekSpendCents) : const Money.zero()) + pendingWeek,
      offlineSpendCeiling: Money(c.offlineCeilingCents),
      policy: CardPolicy.fromJson((jsonDecode(c.policyJson) as Map).cast<String, dynamic>()),
    );
  }
}

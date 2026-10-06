import 'dart:convert';

import 'package:drift/drift.dart';

import '../../core/api/api_client.dart';
import '../../core/db/database.dart';
import '../../core/money/money.dart';

/// Pulls and applies /pos/cache/ (sellers) and /attendance/roster/ (gates),
/// following the documented incremental rules: pass the previous
/// generated_at as ?since=, replace rows by card_uid / id, never delete
/// cards (a retired card arrives with status "lost").
class CacheService {
  CacheService(this.db, this.api);

  final AppDatabase db;
  final PosApi api;

  Future<DateTime?> lastRefresh() async {
    final v = await db.getKv('cache_refreshed_at');
    return v == null ? null : DateTime.parse(v);
  }

  Future<void> refresh({bool full = false}) async {
    final since = full ? null : await db.getKv('cache_generated_at');
    final payload = await api.cache(since: since);
    await apply(payload);
  }

  Future<void> apply(Map<String, dynamic> payload, {DateTime? now}) async {
    final at = (now ?? DateTime.now()).toUtc();
    final cards = (payload['cards'] as List).cast<Map>();
    final products = (payload['products'] as List).cast<Map>();
    final categories = (payload['categories'] as List).cast<Map>();
    final spendDay = payload['spend_day'] as String;
    final weekStart = (payload['week_start'] as String?) ?? spendDay;
    final previousHashes = {
      for (final r in await (db.select(db.cachedCards)..where((t) => t.cardUid.isIn([for (final c in cards) c['card_uid'] as String]))).get())
        r.cardUid: r.pinHash
    };
    await db.transaction(() async {
      // a PIN reset by the school (new hash) clears this device's lockout for that card
      for (final c in cards) {
        final old = previousHashes[c['card_uid']];
        if (old != null && old != c['pin_hash']) {
          await (db.update(db.pinFailures)..where((t) => t.cardUid.equals(c['card_uid'] as String)))
              .write(const PinFailuresCompanion(failures: Value(0), locked: Value(false)));
        }
      }
      if (payload['full'] == true) {
        // a full payload is authoritative for products/categories
        await db.delete(db.products).go();
        await db.delete(db.categories).go();
      }
      await db.batch((b) {
        for (final c in cards) {
          b.insert(
            db.cachedCards,
            CachedCardsCompanion.insert(
              cardUid: c['card_uid'] as String,
              cardId: c['card_id'] as int,
              status: c['status'] as String,
              pinHash: c['pin_hash'] as String,
              studentId: c['student_id'] as int,
              displayName: c['student_display_name'] as String,
              photoUrl: Value(c['photo_url'] as String?),
              schoolId: c['school_id'] as int,
              walletId: c['wallet_id'] as int,
              balanceCents: Money.parse(c['balance'] as String).cents,
              todaySpendCents: Money.parse(c['today_spend'] as String).cents,
              weekSpendCents: Money.parse((c['week_spend'] ?? c['today_spend']) as String).cents,
              spendDay: spendDay,
              weekStart: weekStart,
              offlineCeilingCents: Money.parse(c['offline_spend_ceiling'] as String).cents,
              policyJson: jsonEncode(c['policy']),
              balanceAsOf: at,
            ),
            mode: InsertMode.insertOrReplace,
          );
        }
        for (final p in products) {
          b.insert(
            db.products,
            ProductsCompanion.insert(
              id: Value(p['id'] as int),
              name: p['name'] as String,
              categoryId: p['category_id'] as int,
              categoryName: p['category_name'] as String,
              priceCents: Money.parse(p['price'] as String).cents,
              active: p['active'] == true,
              schoolId: p['school_id'] as int,
              merchantId: Value(p['merchant_id'] as int?),
            ),
            mode: InsertMode.insertOrReplace,
          );
        }
        for (final c in categories) {
          b.insert(
            db.categories,
            CategoriesCompanion.insert(
              id: Value(c['id'] as int),
              name: c['name'] as String,
              isUnhealthy: c['is_unhealthy'] == true,
              active: c['active'] == true,
              schoolId: c['school_id'] as int,
            ),
            mode: InsertMode.insertOrReplace,
          );
        }
      });
      await db.setKv('cache_generated_at', payload['generated_at'] as String);
      await db.setKv('cache_refreshed_at', at.toIso8601String());
      await db.setKv('offline_ceilings', jsonEncode(payload['offline_spend_ceilings']));
      await db.setKv('pin_lockout_threshold', jsonEncode(payload['pin_lockout_threshold']));
    });
    await db.log('cache', true, '${payload['full'] == true ? 'full' : 'incremental'}: ${cards.length} cards, ${products.length} products');
  }

  /// Authoritative balances from a /pos/sync/ or /pos/purchase/ response
  /// replace the cached ones ("overwrite the cached balance with it").
  Future<void> applyBalances(List<Map> balances, {DateTime? now, String? spendDay}) async {
    final at = (now ?? DateTime.now()).toUtc();
    for (final b in balances) {
      await (db.update(db.cachedCards)..where((t) => t.cardUid.equals(b['card_uid'] as String))).write(CachedCardsCompanion(
        status: Value(b['card_status'] as String),
        balanceCents: Value(Money.parse(b['balance'] as String).cents),
        todaySpendCents: Value(Money.parse(b['today_spend'] as String).cents),
        spendDay: spendDay == null ? const Value.absent() : Value(spendDay),
        balanceAsOf: Value(at),
      ));
    }
  }

  // ---- attendance roster ---------------------------------------------------

  Future<void> refreshRoster({bool full = false}) async {
    final since = full ? null : await db.getKv('roster_generated_at');
    final payload = await api.roster(since: since);
    await applyRoster(payload);
  }

  Future<void> applyRoster(Map<String, dynamic> payload) async {
    final cards = (payload['cards'] as List).cast<Map>();
    await db.batch((b) {
      for (final c in cards) {
        b.insert(
          db.rosterCards,
          RosterCardsCompanion.insert(
            cardUid: c['card_uid'] as String,
            status: c['status'] as String,
            studentId: c['student_id'] as int,
            displayName: c['student_display_name'] as String,
            className: (c['class_name'] as String?) ?? '',
            photoUrl: Value(c['photo_url'] as String?),
          ),
          mode: InsertMode.insertOrReplace,
        );
      }
    });
    await db.setKv('roster_generated_at', payload['generated_at'] as String);
    await db.setKv('cache_refreshed_at', DateTime.now().toUtc().toIso8601String());
    await db.log('roster', true, '${cards.length} cards');
  }
}

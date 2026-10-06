import 'dart:io';

import 'package:drift/drift.dart';
import 'package:drift/native.dart';

part 'database.g.dart';

/// Cards from /pos/cache/ (canteen & merchant devices). Money in cents.
class CachedCards extends Table {
  TextColumn get cardUid => text()();
  IntColumn get cardId => integer()();
  TextColumn get status => text()();
  TextColumn get pinHash => text()();
  IntColumn get studentId => integer()();
  TextColumn get displayName => text()();
  TextColumn get photoUrl => text().nullable()();
  IntColumn get schoolId => integer()();
  IntColumn get walletId => integer()();
  IntColumn get balanceCents => integer()();
  IntColumn get todaySpendCents => integer()();
  IntColumn get weekSpendCents => integer()();
  TextColumn get spendDay => text()();
  TextColumn get weekStart => text()();
  IntColumn get offlineCeilingCents => integer()();
  TextColumn get policyJson => text()();
  DateTimeColumn get balanceAsOf => dateTime()();

  @override
  Set<Column> get primaryKey => {cardUid};
}

class Products extends Table {
  IntColumn get id => integer()();
  TextColumn get name => text()();
  IntColumn get categoryId => integer()();
  TextColumn get categoryName => text()();
  IntColumn get priceCents => integer()();
  BoolColumn get active => boolean()();
  IntColumn get schoolId => integer()();
  IntColumn get merchantId => integer().nullable()();

  @override
  Set<Column> get primaryKey => {id};
}

class Categories extends Table {
  IntColumn get id => integer()();
  TextColumn get name => text()();
  BoolColumn get isUnhealthy => boolean()();
  BoolColumn get active => boolean()();
  IntColumn get schoolId => integer()();

  @override
  Set<Column> get primaryKey => {id};
}

/// /attendance/roster/ (attendance devices): display fields only.
class RosterCards extends Table {
  TextColumn get cardUid => text()();
  TextColumn get status => text()();
  IntColumn get studentId => integer()();
  TextColumn get displayName => text()();
  TextColumn get className => text()();
  TextColumn get photoUrl => text().nullable()();

  @override
  Set<Column> get primaryKey => {cardUid};
}

/// Write-ahead sale queue. A row exists BEFORE any network call; it is only
/// marked synced after a confirmed server response. Never deleted unsynced.
///
/// status: pending (to sync) | applied | duplicate | shortfall | rejected
///         | refused (online refusal: the sale did not happen, never synced)
class SaleQueue extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get idempotencyKey => text().unique()();
  TextColumn get cardUid => text()();
  TextColumn get studentName => text()();
  IntColumn get amountCents => integer()();
  TextColumn get itemsJson => text()();
  TextColumn get deviceLocalTimestamp => text()();
  TextColumn get kampalaDay => text()();
  TextColumn get kampalaWeek => text()();
  DateTimeColumn get createdAt => dateTime()();
  TextColumn get channel => text()(); // online | offline
  TextColumn get status => text()();
  IntColumn get appliedCents => integer().nullable()();
  IntColumn get shortfallCents => integer().nullable()();
  TextColumn get flags => text().withDefault(const Constant(''))();
  TextColumn get reason => text().nullable()();
  IntColumn get serverTransactionId => integer().nullable()();
  IntColumn get attempts => integer().withDefault(const Constant(0))();
  TextColumn get lastError => text().nullable()();
  DateTimeColumn get syncedAt => dateTime().nullable()();
}

/// Write-ahead attendance queue. status: pending | created | duplicate | rejected
class AttendanceQueue extends Table {
  IntColumn get id => integer().autoIncrement()();
  TextColumn get idempotencyKey => text().unique()();
  TextColumn get cardUid => text()();
  TextColumn get studentName => text()();
  TextColumn get direction => text()();
  TextColumn get deviceLocalTimestamp => text()();
  TextColumn get kampalaDay => text()();
  DateTimeColumn get createdAt => dateTime()();
  TextColumn get status => text()();
  TextColumn get reason => text().nullable()();
  IntColumn get attempts => integer().withDefault(const Constant(0))();
  DateTimeColumn get syncedAt => dateTime().nullable()();
}

/// Wrong-PIN counters per card on this device (reported via /pos/sync/).
class PinFailures extends Table {
  TextColumn get cardUid => text()();
  IntColumn get failures => integer()();
  IntColumn get unreported => integer()();
  DateTimeColumn get firstFailureAt => dateTime()();
  DateTimeColumn get lastFailureAt => dateTime()();
  BoolColumn get locked => boolean().withDefault(const Constant(false))();

  @override
  Set<Column> get primaryKey => {cardUid};
}

class Kv extends Table {
  TextColumn get key => text()();
  TextColumn get value => text()();

  @override
  Set<Column> get primaryKey => {key};
}

class SyncLog extends Table {
  IntColumn get id => integer().autoIncrement()();
  DateTimeColumn get at => dateTime()();
  TextColumn get kind => text()(); // cache | sales | attendance | roster
  BoolColumn get ok => boolean()();
  TextColumn get message => text()();
}

@DriftDatabase(tables: [CachedCards, Products, Categories, RosterCards, SaleQueue, AttendanceQueue, PinFailures, Kv, SyncLog])
class AppDatabase extends _$AppDatabase {
  AppDatabase(super.e);

  @override
  int get schemaVersion => 1;

  // ---- key/value ---------------------------------------------------------
  Future<String?> getKv(String key) async =>
      (await (select(kv)..where((t) => t.key.equals(key))).getSingleOrNull())?.value;

  Future<void> setKv(String key, String? value) async {
    if (value == null) {
      await (delete(kv)..where((t) => t.key.equals(key))).go();
    } else {
      await into(kv).insertOnConflictUpdate(KvCompanion.insert(key: key, value: value));
    }
  }

  Future<void> log(String kind, bool ok, String message) =>
      into(syncLog).insert(SyncLogCompanion.insert(at: DateTime.now().toUtc(), kind: kind, ok: ok, message: message));

  /// Removes everything except unsynced queue rows (used on re-provisioning
  /// to a different school/device: unsynced records are never deleted).
  Future<void> wipeCache() => transaction(() async {
        await delete(cachedCards).go();
        await delete(products).go();
        await delete(categories).go();
        await delete(rosterCards).go();
        await delete(pinFailures).go();
      });
}

/// Opens the encrypted database file. [hexKey] is a random 256-bit key kept
/// in the platform keystore (flutter_secure_storage); the file is unreadable
/// without it (SQLite3MultipleCiphers, `PRAGMA key`).
QueryExecutor openEncrypted(File file, String hexKey) {
  return NativeDatabase.createInBackground(
    file,
    setup: (db) {
      db.execute("PRAGMA key = \"x'$hexKey'\";");
      // fail fast if the build isn't the cipher-enabled one or the key is wrong
      db.select('SELECT count(*) FROM sqlite_master;');
      db.execute('PRAGMA journal_mode = WAL;');
    },
  );
}

/// In-memory, unencrypted (tests).
AppDatabase memoryDatabase() => AppDatabase(NativeDatabase.memory());

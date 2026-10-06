// Integration test against the RUNNING backend (docker compose + seed_demo).
// Skipped unless SD_LIVE=1:   SD_LIVE=1 flutter test test/live
// It creates its own fixture with `manage.py pos_test_fixture` (fresh
// student, card, canteen + attendance device tokens) and talks to
// http://localhost:8000 exactly as the app does (device-token auth).
import 'dart:convert';
import 'dart:io';

import 'package:drift/drift.dart' hide isNull, isNotNull;
import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_pos/core/api/api_client.dart';
import 'package:schooldimes_pos/core/db/database.dart';
import 'package:schooldimes_pos/core/money/money.dart';
import 'package:schooldimes_pos/core/security/pin_verifier.dart';
import 'package:schooldimes_pos/core/security/secure_store.dart';
import 'package:schooldimes_pos/features/attendance/attendance_service.dart';
import 'package:schooldimes_pos/features/cache/cache_service.dart';
import 'package:schooldimes_pos/features/policy/policy_engine.dart';
import 'package:schooldimes_pos/features/provisioning/provisioning_service.dart';
import 'package:schooldimes_pos/features/sale/sale_service.dart';
import 'package:schooldimes_pos/features/sync/sync_engine.dart';

final base = Platform.environment['SD_API'] ?? 'http://localhost:8000';
final live = Platform.environment['SD_LIVE'] == '1';

Future<Map<String, dynamic>> fixture() async {
  // the running stack's compose project (default: the repo folder name "schooldimes")
  final project = Platform.environment['SD_COMPOSE_PROJECT'] ?? 'schooldimes';
  final r = await Process.run('docker', ['compose', '-p', project, 'exec', '-T', 'web', 'python', 'manage.py', 'pos_test_fixture']);
  if (r.exitCode != 0) throw StateError('pos_test_fixture failed: ${r.stderr}');
  return (jsonDecode((r.stdout as String).trim().split('\n').last) as Map).cast<String, dynamic>();
}

void main() {
  late Map<String, dynamic> fx;
  late AppDatabase db;
  late ApiClient api;

  setUpAll(() async {
    if (!live) return;
    fx = await fixture();
  });

  setUp(() => db = memoryDatabase());
  tearDown(() => db.close());

  test('canteen: provision, cache, online + offline sales, sync, replay, policy agreement', () async {
    final prov = ProvisioningService(MemorySecretStore(), (u, t) => ApiClient(baseUrl: u, token: t));
    final cfg = await prov.provision(baseUrl: base, token: fx['canteen_token'] as String, adminPin: '9999', db: db);
    expect(cfg.role, 'canteen');
    expect(cfg.canSell, isTrue);
    api = ApiClient(baseUrl: base, token: cfg.token);

    // 1. full cache
    final cache = CacheService(db, api);
    await cache.refresh(full: true);
    final uid = fx['card_uid'] as String;
    final sales = SaleService(db: db, api: api, verifier: PinVerifier(preferNative: false), merchantId: null);
    var (lookup, card) = await sales.lookup(uid);
    expect(lookup, LookupResult.ok);
    expect(card!.balanceCents, Money.parse(fx['balance'] as String).cents);

    // 2. the REAL Django hash verifies on the device (870k iterations)
    expect((await sales.checkPin(card, '0000', 5)).$1, PinResult.wrong);
    expect((await sales.checkPin(card, fx['pin'] as String, 5)).$1, PinResult.ok);

    // 3. online sale with a product line item
    final product = await (db.select(db.products)..where((p) => p.active.equals(true))..limit(1)).getSingle();
    final line = SaleLine(productId: product.id, categoryId: product.categoryId, quantity: 1, unitPrice: Money(product.priceCents), description: product.name);
    final state = await sales.cards.stateOf(card);
    final online = await sales.commit(card, line.lineTotal, [line], online: true);
    expect(online.refused, isFalse, reason: '${online.code} ${online.detail}');
    expect(online.channel, SaleChannel.online);
    expect(online.newBalance, state.balance - line.lineTotal);

    // 4. offline sale (custom amount) -> queued, estimated balance
    (_, card) = await sales.lookup(uid);
    final custom = SaleLine(quantity: 2, unitPrice: Money.parse('250'), description: 'Mandazi');
    final offline = await sales.commit(card!, custom.lineTotal, [custom], online: false);
    expect(offline.channel, SaleChannel.offline);
    expect(offline.newBalance, online.newBalance! - custom.lineTotal);

    // 5. sync: applied; authoritative balance equals the estimate
    final sync = SyncEngine(db: db, api: api, canSell: true, canRecordAttendance: false);
    final r1 = await sync.run(manual: true);
    expect(r1.applied, 1, reason: r1.toString());
    (_, card) = await sales.lookup(uid);
    expect(Money(card!.balanceCents), offline.newBalance);

    // 6. a replayed batch has no double effect
    await (db.update(db.saleQueue)..where((s) => s.channel.equals('offline'))).write(const SaleQueueCompanion(status: Value('pending')));
    final r2 = await sync.run(manual: true);
    expect(r2.duplicates, 1);
    (_, card) = await sales.lookup(uid);
    expect(Money(card!.balanceCents), offline.newBalance);

    // 7. offline decision == server decision for the same input
    final s = await sales.cards.stateOf(card);
    final cap = s.policy.dailySpendCap;
    if (cap != null) {
      final over = cap - s.todaySpend + Money.parse('100');
      final local = purchaseViolations(s, over, [], strictBalance: true);
      expect(local, contains('daily_cap_exceeded'));
      final refused = await sales.commit(card, over, [SaleLine(quantity: 1, unitPrice: over, description: 'Over cap')], online: true);
      expect(refused.refused, isTrue);
      expect(refused.code, local.first, reason: 'server ${refused.code} vs device $local');
    }
  }, skip: live ? false : 'set SD_LIVE=1 with the backend running', timeout: const Timeout(Duration(minutes: 3)));

  test('attendance: provision, roster, taps queued offline, synced once, replay is duplicate', () async {
    final prov = ProvisioningService(MemorySecretStore(), (u, t) => ApiClient(baseUrl: u, token: t));
    final cfg = await prov.provision(baseUrl: base, token: fx['attendance_token'] as String, adminPin: '9999', db: db);
    expect(cfg.role, 'attendance');
    expect(cfg.canRecordAttendance, isTrue);
    api = ApiClient(baseUrl: base, token: cfg.token);
    await CacheService(db, api).refreshRoster(full: true);
    final svc = AttendanceService(db);
    final tap = await svc.tap(fx['card_uid'] as String, 'in');
    expect(tap.status, TapStatus.recorded);
    expect(tap.card!.displayName, startsWith('POS E2E Student'));
    final sync = SyncEngine(db: db, api: api, canSell: false, canRecordAttendance: true);
    expect((await sync.run(manual: true)).tapsCreated, 1);
    await db.update(db.attendanceQueue).write(const AttendanceQueueCompanion(status: Value('pending')));
    final again = await sync.run(manual: true);
    expect(again.tapsCreated, 0);
    expect((await db.select(db.attendanceQueue).get()).single.status, 'duplicate');
  }, skip: live ? false : 'set SD_LIVE=1 with the backend running');
}

import 'package:drift/drift.dart' hide isNull, isNotNull;
import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_pos/core/api/api_client.dart';
import 'package:schooldimes_pos/core/db/database.dart';
import 'package:schooldimes_pos/core/money/money.dart';
import 'package:schooldimes_pos/core/security/pin_verifier.dart';
import 'package:schooldimes_pos/features/cache/cache_service.dart';
import 'package:schooldimes_pos/features/policy/policy_engine.dart';
import 'package:schooldimes_pos/features/sale/sale_service.dart';
import 'package:schooldimes_pos/features/sync/sync_engine.dart';

import 'support/fake_api.dart';

final rice = SaleLine(productId: 5, categoryId: 3, quantity: 1, unitPrice: Money.parse('3000'), description: 'Rice & beans');
final soda = SaleLine(productId: 6, categoryId: 2, quantity: 1, unitPrice: Money.parse('1500'), description: 'Soda');

void main() {
  late AppDatabase db;
  late FakePosApi api;
  late SaleService sales;
  late SyncEngine sync;

  setUp(() async {
    db = memoryDatabase();
    api = FakePosApi()..cachePayload = cachePayload();
    await CacheService(db, api).refresh(full: true);
    sales = SaleService(db: db, api: api, verifier: PinVerifier(preferNative: false), merchantId: null);
    sync = SyncEngine(db: db, api: api, canSell: true, canRecordAttendance: false);
  });
  tearDown(() => db.close());

  Future<List<SaleQueueData>> queue() => db.select(db.saleQueue).get();

  group('cache', () {
    test('full then incremental refresh (?since= the previous generated_at)', () async {
      expect((await db.select(db.cachedCards).get()).single.balanceCents, 1000000);
      api.cachePayload = cachePayload(full: false, generatedAt: '2026-10-05T08:00:00+00:00', cards: [card(status: 'frozen')], products: []);
      await CacheService(db, api).refresh();
      expect(api.cacheSinces.last, '2026-10-05T07:00:00+00:00');
      expect((await db.select(db.cachedCards).get()).single.status, 'frozen');
      expect(await db.select(db.products).get(), hasLength(2)); // incremental keeps rows not re-sent
    });
  });

  group('card lookup & PIN', () {
    test('frozen / lost / unknown are refused before any PIN prompt', () async {
      expect((await sales.lookup('ffffffff')).$1, LookupResult.unknownCard);
      api.cachePayload = cachePayload(cards: [card(status: 'lost')]);
      await CacheService(db, api).refresh(full: true);
      expect((await sales.lookup('04aabbcc')).$1, LookupResult.lost);
    });

    test('wrong PINs lock the card on this device and are reported on sync', () async {
      final (_, c) = await sales.lookup('04aabbcc');
      expect((await sales.checkPin(c!, '0000', 3)).$1, PinResult.wrong);
      expect((await sales.checkPin(c, '1111', 3)).$1, PinResult.wrong);
      expect((await sales.checkPin(c, '2222', 3)).$1, PinResult.locked);
      expect((await sales.lookup('04aabbcc')).$1, LookupResult.lockedOnDevice);
      await sync.run(manual: true, refreshCache: false);
      expect(api.pinReportCalls.single, [
        {'card_uid': '04aabbcc', 'failed_attempts': 3, 'device_local_timestamp': isA<String>()}
      ]);
      await sync.run(manual: true, refreshCache: false);
      expect(api.pinReportCalls.length, 1); // reported once only
    });

    test('correct PIN', () async {
      final (_, c) = await sales.lookup('04aabbcc');
      expect((await sales.checkPin(c!, '5555', 3)).$1, PinResult.ok);
    });

    test('a PIN reset by the school (new hash) clears the device lockout', () async {
      final (_, c) = await sales.lookup('04aabbcc');
      for (final p in ['1', '2', '3']) {
        await sales.checkPin(c!, p, 3);
      }
      api.cachePayload = cachePayload(full: false, cards: [card(pinHash: r'pbkdf2_sha256$1$other$abc=')]);
      await CacheService(db, api).refresh();
      expect((await sales.lookup('04aabbcc')).$1, isNot(LookupResult.lockedOnDevice));
    });
  });

  group('local checks use cached numbers adjusted by unsynced sales', () {
    test('blocked category and daily cap across offline sales', () async {
      final (_, c) = await sales.lookup('04aabbcc');
      expect(await sales.check(c!, Money.parse('1500'), [soda]), ['category_blocked']);
      await sales.commit(c, Money.parse('3000'), [rice], online: false);
      // 3000 spent today offline; 3000 more breaks the 5000 daily cap
      expect(await sales.check(c, Money.parse('3000'), [rice]), ['daily_cap_exceeded']);
      final state = await sales.cards.stateOf(c);
      expect(state.balance, Money.parse('7000'));
    });
  });

  group('sale commit', () {
    test('offline: written to the queue before anything else', () async {
      final (_, c) = await sales.lookup('04aabbcc');
      final out = await sales.commit(c!, Money.parse('3000'), [rice], online: false);
      expect(out.channel, SaleChannel.offline);
      expect(api.purchaseCalls, isEmpty);
      final q = await queue();
      expect(q.single.status, 'pending');
      expect(q.single.idempotencyKey, out.key);
    });

    test('online success: applied, balance authoritative', () async {
      final (_, c) = await sales.lookup('04aabbcc');
      final out = await sales.commit(c!, Money.parse('3000'), [rice], online: true);
      expect(out.channel, SaleChannel.online);
      expect(out.newBalance, Money.parse('7000'));
      expect(api.purchaseCalls.single['pin_verified'], isTrue);
      expect(api.purchaseCalls.single.containsKey('pin'), isFalse); // the raw PIN never leaves the device
      expect((await queue()).single.status, 'applied');
    });

    test('online refusal: nothing happened, never synced', () async {
      api.purchaseRefusal = (_) => ApiException(statusCode: 422, code: 'insufficient_funds', detail: 'Insufficient funds.', body: {'code': 'insufficient_funds', 'violations': ['insufficient_funds']});
      final (_, c) = await sales.lookup('04aabbcc');
      final out = await sales.commit(c!, Money.parse('3000'), [rice], online: true);
      expect(out.refused, isTrue);
      expect(out.code, 'insufficient_funds');
      await sync.run(manual: true, refreshCache: false);
      expect(api.syncCalls.isEmpty || api.syncCalls.every((b) => b.isEmpty), isTrue);
    });

    test('timeout AFTER the server applied it: queued with the same key -> duplicate, never charged twice', () async {
      api
        ..failNextPurchase = ApiException(timeout: true)
        ..purchaseTimesOutAfterServerApplies = true;
      final (_, c) = await sales.lookup('04aabbcc');
      final out = await sales.commit(c!, Money.parse('3000'), [rice], online: true);
      expect(out.channel, SaleChannel.offline);
      expect((await queue()).single.status, 'pending');
      final report = await sync.run(manual: true, refreshCache: false);
      expect(api.syncCalls.single.single['idempotency_key'], out.key);
      expect(report.duplicates, 1);
      expect(api.serverSales.length, 1);
      expect((await queue()).single.status, 'duplicate');
    });

    test('a device revoked mid-sale stops transacting', () async {
      api.failNextPurchase = ApiException(statusCode: 401, detail: 'Invalid or revoked device token.');
      final (_, c) = await sales.lookup('04aabbcc');
      await expectLater(sales.commit(c!, Money.parse('3000'), [rice], online: true), throwsA(isA<DeviceRevoked>()));
    });
  });

  group('sync engine', () {
    Future<void> offlineSales(int n) async {
      final (_, c) = await sales.lookup('04aabbcc');
      for (var i = 0; i < n; i++) {
        await sales.commit(c!, Money.parse('100'), [SaleLine(quantity: 1, unitPrice: Money.parse('100'), description: 'Mandazi')], online: false);
      }
    }

    test('oldest first, per-item results, balances applied', () async {
      await offlineSales(3);
      var n = 0;
      api.syncResult = (tx) {
        n++;
        if (n == 2) {
          return {'idempotency_key': tx['idempotency_key'], 'status': 'shortfall', 'transaction_id': 9, 'amount': '100.00', 'applied_amount': '40.00', 'shortfall_amount': '60.00', 'flags': ['exceeds_offline_ceiling'], 'reason': null};
        }
        if (n == 3) return {'idempotency_key': tx['idempotency_key'], 'status': 'rejected', 'transaction_id': 10, 'amount': '100.00', 'applied_amount': '0.00', 'shortfall_amount': '0.00', 'flags': [], 'reason': 'amount_mismatch'};
        return {'idempotency_key': tx['idempotency_key'], 'status': 'applied', 'transaction_id': 8, 'amount': '100.00', 'applied_amount': '100.00', 'shortfall_amount': '0.00', 'flags': [], 'reason': null};
      };
      final report = await sync.run(manual: true, refreshCache: false);
      expect([report.applied, report.shortfalls, report.rejected], [1, 1, 1]);
      final q = await (db.select(db.saleQueue)..orderBy([(t) => OrderingTerm.asc(t.id)])).get();
      expect(q.map((s) => s.status), ['applied', 'shortfall', 'rejected']);
      expect(q[1].shortfallCents, 6000);
      expect(q[2].reason, 'amount_mismatch');
      expect(api.syncCalls.single.map((t) => t['idempotency_key']), q.map((s) => s.idempotencyKey)); // oldest first
      expect((await db.select(db.cachedCards).get()).single.balanceCents, 100000); // overwritten from the response
    });

    test('a network failure leaves every record queued, then a retry sends the same keys', () async {
      await offlineSales(2);
      api.failNextSync = ApiException(network: true);
      final failed = await sync.run(manual: true, refreshCache: false);
      expect(failed.networkFailed, isTrue);
      expect((await queue()).every((s) => s.status == 'pending'), isTrue);
      expect(sync.backingOff, isTrue);
      expect((await sync.run()).error, 'backoff'); // automatic triggers wait
      await sync.run(manual: true, refreshCache: false); // "Sync now" doesn't
      expect(api.syncCalls[1].map((t) => t['idempotency_key']), api.syncCalls[0].map((t) => t['idempotency_key']));
      expect((await queue()).every((s) => s.status == 'applied'), isTrue);
    });

    test('a replayed batch causes no duplicates', () async {
      await offlineSales(2);
      await sync.run(manual: true, refreshCache: false);
      // simulate a lost response: put rows back to pending and sync again
      await db.update(db.saleQueue).write(const SaleQueueCompanion(status: Value('pending')));
      final r = await sync.run(manual: true, refreshCache: false);
      expect(r.duplicates, 2);
      expect(api.serverSales.length, 2);
    });

    test('batches respect the batch size', () async {
      sync = SyncEngine(db: db, api: api, canSell: true, canRecordAttendance: false, batchSize: 2);
      await offlineSales(5);
      await sync.run(manual: true, refreshCache: false);
      expect(api.syncCalls.map((b) => b.length), [2, 2, 1]);
    });

    test('synced rows are pruned after retention, pending never', () async {
      sync = SyncEngine(db: db, api: api, canSell: true, canRecordAttendance: false, retention: const Duration(seconds: -5));
      await offlineSales(1);
      await sync.run(manual: true, refreshCache: false);
      expect(await queue(), isEmpty);
      api.failNextSync = ApiException(network: true);
      await offlineSales(1);
      await sync.run(manual: true, refreshCache: false);
      expect((await queue()).single.status, 'pending');
    });

    test('backoff grows exponentially with jitter and caps at 10 min', () {
      final b1 = sync.backoffFor(1).inMilliseconds, b5 = sync.backoffFor(5).inMilliseconds, b20 = sync.backoffFor(20).inMilliseconds;
      expect(b1, inInclusiveRange(2500, 7500));
      expect(b5, inInclusiveRange(40000, 120000));
      expect(b20, lessThanOrEqualTo(900000));
    });
  });
}

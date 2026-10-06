import 'dart:convert';

import 'package:drift/drift.dart';
import 'package:uuid/uuid.dart';

import '../../core/api/api_client.dart';
import '../../core/db/database.dart';
import '../../core/money/money.dart';
import '../../core/security/pin_verifier.dart';
import '../../core/time/kampala.dart';
import '../cache/cache_service.dart';
import '../cache/card_repository.dart';
import '../policy/policy_engine.dart';
import 'pin_guard.dart';

enum LookupResult { ok, unknownCard, frozen, lost, lockedOnDevice, onlineOnly }

enum PinResult { ok, wrong, locked }

enum SaleChannel { online, offline }

/// What happened to a confirmed sale.
class SaleOutcome {
  SaleOutcome.done({required this.channel, required this.key, required this.newBalance, this.serverStatus, this.flags = const []})
      : refused = false,
        code = null,
        detail = null;
  SaleOutcome.refused({required this.key, required this.code, this.detail})
      : refused = true,
        channel = SaleChannel.online,
        newBalance = null,
        serverStatus = null,
        flags = const [];

  final bool refused;
  final SaleChannel channel;
  final String key;

  /// Authoritative (online) or estimated (offline) balance after the sale.
  final Money? newBalance;
  final String? serverStatus;
  final List<String> flags;
  final String? code;
  final String? detail;
}

class DeviceRevoked implements Exception {}

class SaleService {
  SaleService({required this.db, required this.api, required this.verifier, required this.merchantId, Uuid? uuid})
      : cards = CardRepository(db),
        pins = PinGuard(db),
        cache = CacheService(db, api),
        _uuid = uuid ?? const Uuid();

  final AppDatabase db;
  final PosApi api;
  final PinVerifier verifier;
  final int? merchantId;
  final CardRepository cards;
  final PinGuard pins;
  final CacheService cache;
  final Uuid _uuid;

  /// Card states that are refused before any PIN is asked (no PIN prompt for
  /// frozen/lost cards, per the brief).
  Future<(LookupResult, CachedCard?)> lookup(String uid) async {
    final card = await cards.find(uid);
    if (card == null) return (LookupResult.unknownCard, null);
    if (card.status == 'frozen') return (LookupResult.frozen, card);
    if (card.status == 'lost') return (LookupResult.lost, card);
    if (await pins.isLocked(uid)) return (LookupResult.lockedOnDevice, card);
    if (!PinVerifier.canVerifyOffline(card.pinHash)) return (LookupResult.onlineOnly, card);
    return (LookupResult.ok, card);
  }

  Future<(PinResult, int)> checkPin(CachedCard card, String pin, int threshold) async {
    if (await verifier.verify(pin, card.pinHash)) {
      await pins.recordSuccess(card.cardUid);
      return (PinResult.ok, threshold);
    }
    final left = await pins.recordFailure(card.cardUid, threshold);
    return (left == 0 ? PinResult.locked : PinResult.wrong, left);
  }

  /// Local policy checks (mirror of the backend's debit_violations()).
  Future<List<String>> check(CachedCard card, Money amount, List<SaleLine> lines) async =>
      purchaseViolations(await cards.stateOf(card), amount, lines, merchantId: merchantId);

  static List<Map<String, dynamic>> itemsJson(List<SaleLine> lines) => [
        for (final l in lines)
          l.productId != null
              ? {'product_id': l.productId, 'quantity': l.quantity, 'unit_price': l.unitPrice.toApi(), 'description': ?l.description}
              : {'description': l.description ?? 'Item', 'category_id': ?l.categoryId, 'quantity': l.quantity, 'unit_price': l.unitPrice.toApi()},
      ];

  /// Records a confirmed sale. The row is written BEFORE any network call.
  /// Online: POST /pos/purchase/ (server authorises in real time). On no
  /// response / timeout the sale stays queued with the SAME key and goes out
  /// through /pos/sync/: a request that did reach the server comes back as
  /// "duplicate", never as a second charge.
  Future<SaleOutcome> commit(CachedCard card, Money amount, List<SaleLine> lines, {required bool online, DateTime? now}) async {
    final at = (now ?? DateTime.now()).toUtc();
    final key = _uuid.v4();
    final items = itemsJson(lines);
    final body = {
      'idempotency_key': key,
      'card_uid': card.cardUid,
      'amount': amount.toApi(),
      'items': items,
      'device_local_timestamp': Kampala.isoLocal(at),
      'pin_verified': true,
    };
    final id = await db.into(db.saleQueue).insert(SaleQueueCompanion.insert(
          idempotencyKey: key,
          cardUid: card.cardUid,
          studentName: card.displayName,
          amountCents: amount.cents,
          itemsJson: jsonEncode(items),
          deviceLocalTimestamp: body['device_local_timestamp'] as String,
          kampalaDay: Kampala.day(at),
          kampalaWeek: Kampala.weekStart(at),
          createdAt: at,
          channel: online ? 'online' : 'offline',
          status: 'pending',
        ));
    final row = db.update(db.saleQueue)..where((t) => t.id.equals(id));

    if (online) {
      try {
        final r = await api.purchase(body);
        final status = r['status'] as String;
        await row.write(SaleQueueCompanion(
          status: Value(status == 'duplicate' ? 'duplicate' : status),
          appliedCents: Value(Money.parse(r['applied_amount'] as String).cents),
          shortfallCents: Value(Money.parse(r['shortfall_amount'] as String).cents),
          flags: Value(((r['flags'] as List?) ?? const []).join(',')),
          serverTransactionId: Value(r['transaction_id'] as int?),
          syncedAt: Value(DateTime.now().toUtc()),
        ));
        final balance = (r['balance'] as Map?)?.cast<String, dynamic>();
        if (balance != null) await cache.applyBalances([balance]);
        return SaleOutcome.done(
          channel: SaleChannel.online,
          key: key,
          newBalance: balance == null ? null : Money.parse(balance['balance'] as String),
          serverStatus: status,
          flags: List<String>.from((r['flags'] as List?) ?? const []),
        );
      } on ApiException catch (e) {
        if (e.revoked) {
          await row.write(const SaleQueueCompanion(status: Value('refused'), reason: Value('device_revoked')));
          throw DeviceRevoked();
        }
        if (!e.unreachable) {
          // a definite answer: refused (debit gate) or rejected (bad data) -- nothing recorded server-side
          final rejected = e.body is Map && (e.body as Map)['status'] == 'rejected';
          await row.write(SaleQueueCompanion(
            status: Value(rejected ? 'rejected' : 'refused'),
            reason: Value(e.code),
            lastError: Value(e.detail),
            syncedAt: Value(DateTime.now().toUtc()),
          ));
          return SaleOutcome.refused(key: key, code: e.code ?? 'error', detail: e.detail);
        }
        // fall through: may or may not have reached the server -> offline with the same key
        await row.write(SaleQueueCompanion(channel: const Value('offline'), lastError: Value(e.toString())));
      }
    }
    final state = await cards.stateOf(card, now: at);
    return SaleOutcome.done(channel: SaleChannel.offline, key: key, newBalance: state.balance);
  }
}

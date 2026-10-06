import 'dart:async';

import 'package:uuid/uuid.dart';

import '../../core/api/api_client.dart';
import '../../core/api/parent_api.dart';
import '../../core/config/env.dart';

/// One top-up the parent is making. The idempotency key is created once and
/// reused for every retry of the SAME action (flaky mobile data), so a
/// retry returns the original deposit instead of charging again. A new key
/// only comes with [startOver].
class DepositDraft {
  DepositDraft({Uuid? uuid}) : _uuid = uuid ?? const Uuid() {
    key = _uuid.v4();
  }

  final Uuid _uuid;
  late String key;
  Json? created;

  /// Submits (or re-submits after a network error) with the same key.
  Future<Json> submit(ParentApi api, {required int walletId, required String amount, required String channel, String? payerPhone}) async {
    created = await api.createDeposit({
      'wallet': walletId,
      'amount': amount,
      'channel': channel,
      if (payerPhone != null && payerPhone.isNotEmpty) 'payer_phone': payerPhone,
      'idempotency_key': key,
    });
    return created!;
  }

  void startOver() {
    key = _uuid.v4();
    created = null;
  }
}

/// Polls GET /payments/deposits/{id}/ until it leaves "pending".
Stream<Json> pollDeposit(ParentApi api, int id, {Duration every = Env.depositPollEvery, Duration giveUpAfter = Env.depositPollFor}) async* {
  final end = DateTime.now().add(giveUpAfter);
  while (true) {
    try {
      final d = await api.deposit(id);
      yield d;
      if (d['status'] != 'pending') return;
    } on ApiException catch (e) {
      if (!e.network) rethrow; // keep polling through flaky data
    }
    if (DateTime.now().isAfter(end)) return;
    await Future<void>.delayed(every);
  }
}

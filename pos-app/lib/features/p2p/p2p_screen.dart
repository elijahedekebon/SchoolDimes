import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../app/services.dart';
import '../../app/session.dart';
import '../../core/api/api_client.dart';
import '../../core/db/database.dart';
import '../../core/money/money.dart';
import '../../core/ui/widgets.dart';
import '../sale/card_flow.dart';
import '../sale/sale_service.dart';

/// Student-to-student transfer at a canteen till (DECISIONS.md, Part 2 §C:
/// the sender presents card + PIN). Online only: POST /pos/p2p-transfer/.
/// The PIN is checked on the device first (lockout counting); the contract
/// also requires it on the request, so it is kept in memory for that one
/// call and then dropped.
class P2PScreen extends ConsumerStatefulWidget {
  const P2PScreen({super.key});
  @override
  ConsumerState<P2PScreen> createState() => _P2PScreenState();
}

class _P2PScreenState extends ConsumerState<P2PScreen> {
  CachedCard? _sender, _receiver;
  String? _pin;
  String _amount = '';
  final _note = TextEditingController();
  String? _key;
  bool _busy = false;
  String? _message;

  void _reset() => setState(() {
        _sender = _receiver = null;
        _pin = _key = _message = null;
        _amount = '';
        _note.clear();
      });

  Future<void> _start() async {
    final l = context.l;
    if (!(ref.read(statusProvider).value?.online ?? false)) {
      showError(context, l.p2pOnlineOnly);
      return;
    }
    final sender = await CardTapPage.open(context, title: l.p2pTitle, subtitle: l.p2pSenderTap, requirePin: false);
    if (sender == null || !mounted) return;
    final pin = await _askPin(sender);
    if (pin == null || !mounted) return;
    final receiver = await CardTapPage.open(context, title: l.p2pTitle, subtitle: l.p2pReceiverTap, requirePin: false, excludeUid: sender.cardUid);
    if (receiver == null || !mounted) return;
    setState(() {
      _sender = sender;
      _pin = pin;
      _receiver = receiver;
      _key = const Uuid().v4(); // one key per transfer; reused on retry
    });
  }

  Future<String?> _askPin(CachedCard card) async {
    var pin = '';
    String? error;
    final threshold = ref.read(sessionProvider).requireValue.config!.pinLockoutThreshold;
    return showDialog<String>(
      context: context,
      builder: (c) => StatefulBuilder(builder: (c, set) {
        return AlertDialog(
          title: Text('${card.displayName} — ${context.l.enterPin}'),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            Text(List.filled(pin.length, '●').join(' '), style: const TextStyle(fontSize: 28)),
            if (error != null) Text(error!, style: const TextStyle(color: Colors.red)),
            NumPad(
              onKey: (k) => pin.length < 6 ? set(() => pin += k) : null,
              onBackspace: () => pin.isNotEmpty ? set(() => pin = pin.substring(0, pin.length - 1)) : null,
              onDone: () async {
                final (r, left) = await ref.read(saleServiceProvider).checkPin(card, pin, threshold);
                if (!c.mounted) return;
                if (r == PinResult.ok) {
                  Navigator.pop(c, pin);
                } else if (r == PinResult.locked) {
                  Navigator.pop(c);
                  showError(context, context.l.pinLocked);
                } else {
                  set(() {
                    error = context.l.pinWrong(left);
                    pin = '';
                  });
                }
              },
              doneLabel: context.l.confirm,
            ),
          ]),
        );
      }),
    );
  }

  Future<void> _send() async {
    final amount = Money.tryParse(_amount);
    if (amount == null || !amount.isPositive || _sender == null) return;
    setState(() {
      _busy = true;
      _message = null;
    });
    final api = ref.read(sessionProvider).requireValue.api!;
    try {
      await api.p2pTransfer({
        'idempotency_key': _key,
        'sender_card_uid': _sender!.cardUid,
        'pin': _pin,
        'recipient_card_uid': _receiver!.cardUid,
        'amount': amount.toApi(),
        'note': _note.text.trim(),
      });
      if (!mounted) return;
      final done = context.l.p2pDone(amount.format(), _receiver!.displayName);
      _reset();
      ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(done), backgroundColor: Colors.green.shade700));
      ref.read(syncControllerProvider).run(); // pick up new balances
    } on ApiException catch (e) {
      if (!mounted) return;
      if (e.revoked) {
        await ref.read(sessionProvider.notifier).markRevoked();
      } else {
        setState(() => _message = e.unreachable ? context.l.p2pOnlineOnly : (e.detail ?? reasonText(context.l, e.code)));
      }
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  void dispose() {
    _pin = null;
    _note.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final theme = Theme.of(context);
    final amount = Money.tryParse(_amount);
    return Column(children: [
      const StatusBar(),
      Expanded(
        child: _sender == null
            ? Center(
                child: FilledButton.icon(key: const Key('p2p-start'), onPressed: _start, icon: const Icon(Icons.swap_horiz), label: Text(l.p2pTitle)),
              )
            : ListView(padding: const EdgeInsets.all(16), children: [
                Text('${_sender!.displayName}  →  ${_receiver!.displayName}', style: theme.textTheme.titleLarge, textAlign: TextAlign.center),
                const SizedBox(height: 16),
                Text(l.p2pAmount, textAlign: TextAlign.center),
                Text(amount == null ? '—' : amount.format(), style: theme.textTheme.displaySmall, textAlign: TextAlign.center),
                TextField(controller: _note, decoration: InputDecoration(labelText: l.p2pNote)),
                if (_message != null) Padding(padding: const EdgeInsets.all(8), child: Text(_message!, style: TextStyle(color: theme.colorScheme.error), textAlign: TextAlign.center)),
                const SizedBox(height: 8),
                NumPad(
                  onKey: (k) => setState(() => _amount += k),
                  onBackspace: () => _amount.isNotEmpty ? setState(() => _amount = _amount.substring(0, _amount.length - 1)) : null,
                  onDone: amount != null && amount.isPositive && !_busy ? _send : null,
                  doneLabel: amount == null ? l.confirm : l.p2pSend(amount.format()),
                ),
                TextButton(onPressed: _busy ? null : _reset, child: Text(l.cancel)),
              ]),
      ),
    ]);
  }
}

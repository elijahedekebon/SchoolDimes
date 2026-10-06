import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/services.dart';
import '../../app/session.dart';
import '../../core/config/env.dart';
import '../../core/db/database.dart';
import '../../core/nfc/nfc_reader.dart';
import '../../core/nfc/uid.dart';
import '../../core/ui/widgets.dart';
import 'sale_service.dart';

/// Full-screen "tap card → PIN" step. Pops with the verified card, or null.
/// Frozen / lost / unknown / locked cards are refused with no PIN prompt.
class CardTapPage extends ConsumerStatefulWidget {
  const CardTapPage({super.key, required this.title, this.subtitle, this.requirePin = true, this.excludeUid});
  final String title;
  final String? subtitle;
  final bool requirePin;
  final String? excludeUid;

  static Future<CachedCard?> open(BuildContext context, {required String title, String? subtitle, bool requirePin = true, String? excludeUid}) =>
      Navigator.of(context).push<CachedCard>(MaterialPageRoute(
          fullscreenDialog: true,
          builder: (_) => CardTapPage(title: title, subtitle: subtitle, requirePin: requirePin, excludeUid: excludeUid)));

  @override
  ConsumerState<CardTapPage> createState() => _CardTapPageState();
}

class _CardTapPageState extends ConsumerState<CardTapPage> {
  StreamSubscription<String>? _sub;
  StreamSubscription<void>? _bad;
  NfcState? _nfc;
  String? _message;
  CachedCard? _card;
  String _pin = '';
  bool _checking = false;
  final _simCtl = TextEditingController();

  @override
  void initState() {
    super.initState();
    final reader = ref.read(nfcReaderProvider);
    _sub = reader.uids.listen(_onUid);
    _bad = reader.unsupportedTags.listen((_) => setState(() => _message = context.l.unsupportedTag));
    reader.start().then((s) => mounted ? setState(() => _nfc = s) : null);
  }

  @override
  void dispose() {
    _sub?.cancel();
    _bad?.cancel();
    _simCtl.dispose();
    super.dispose();
  }

  Future<void> _onUid(String uid) async {
    if (_card != null || _checking) return;
    final l = context.l;
    if (uid == widget.excludeUid) {
      setState(() => _message = l.p2pSameCard);
      return;
    }
    final (result, card) = await ref.read(saleServiceProvider).lookup(uid);
    if (!mounted) return;
    final msg = switch (result) {
      LookupResult.ok => null,
      LookupResult.unknownCard => l.cardUnknown,
      LookupResult.frozen => l.cardFrozen,
      LookupResult.lost => l.cardLost,
      LookupResult.lockedOnDevice => l.cardLockedOnDevice,
      LookupResult.onlineOnly => l.cardOnlineOnly,
    };
    if (msg != null) {
      setState(() => _message = msg);
      return;
    }
    if (!widget.requirePin) {
      Navigator.of(context).pop(card);
      return;
    }
    setState(() {
      _card = card;
      _message = null;
      _pin = '';
    });
  }

  Future<void> _checkPin() async {
    if (_pin.length < 4 || _card == null) return;
    setState(() => _checking = true);
    final threshold = ref.read(sessionProvider).requireValue.config!.pinLockoutThreshold;
    final (result, left) = await ref.read(saleServiceProvider).checkPin(_card!, _pin, threshold);
    if (!mounted) return;
    final l = context.l;
    setState(() {
      _checking = false;
      _pin = '';
    });
    switch (result) {
      case PinResult.ok:
        Navigator.of(context).pop(_card);
      case PinResult.wrong:
        setState(() => _message = l.pinWrong(left));
      case PinResult.locked:
        setState(() {
          _message = l.pinLocked;
          _card = null;
        });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      body: Column(children: [
        const StatusBar(),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: _card == null ? _tapView(theme) : _pinView(theme),
          ),
        ),
      ]),
    );
  }

  Widget _tapView(ThemeData theme) => Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          if (widget.subtitle != null) Text(widget.subtitle!, style: theme.textTheme.titleLarge, textAlign: TextAlign.center),
          const SizedBox(height: 24),
          Icon(Icons.contactless, size: 120, color: theme.colorScheme.primary),
          const SizedBox(height: 16),
          Text(context.l.tapCard, style: theme.textTheme.headlineSmall, textAlign: TextAlign.center),
          Text(context.l.tapCardHint, textAlign: TextAlign.center),
          if (_nfc == NfcState.disabled) Padding(padding: const EdgeInsets.only(top: 16), child: Text(context.l.nfcDisabled, style: TextStyle(color: theme.colorScheme.error))),
          if (_nfc == NfcState.unsupported && !Env.isDev) Padding(padding: const EdgeInsets.only(top: 16), child: Text(context.l.nfcUnsupported, style: TextStyle(color: theme.colorScheme.error))),
          if (_message != null)
            Padding(
              padding: const EdgeInsets.only(top: 24),
              child: Text(_message!, key: const Key('card-message'), style: theme.textTheme.titleMedium?.copyWith(color: theme.colorScheme.error), textAlign: TextAlign.center),
            ),
          // dev flavor only: type a UID instead of tapping (tree-shaken from prod)
          if (Env.isDev) ...[
            const SizedBox(height: 32),
            Row(children: [
              Expanded(child: TextField(key: const Key('simulate-uid'), controller: _simCtl, decoration: InputDecoration(labelText: context.l.simulateTap, hintText: context.l.simulateTapHint))),
              const SizedBox(width: 8),
              FilledButton(
                key: const Key('simulate-tap'),
                onPressed: () {
                  final uid = normalizeUid(_simCtl.text);
                  if (uid != null) ref.read(nfcReaderProvider).emit(uid);
                },
                child: const Icon(Icons.nfc),
              ),
            ]),
          ],
        ],
      );

  Widget _pinView(ThemeData theme) => Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Text(_card!.displayName, style: theme.textTheme.headlineSmall),
          const SizedBox(height: 8),
          Text(context.l.enterPin, style: theme.textTheme.titleMedium),
          const SizedBox(height: 16),
          Text(List.filled(_pin.length, '●').join(' ').padRight(1), key: const Key('pin-dots'), style: const TextStyle(fontSize: 32, letterSpacing: 4)),
          if (_message != null) Padding(padding: const EdgeInsets.all(8), child: Text(_message!, key: const Key('card-message'), style: TextStyle(color: theme.colorScheme.error))),
          if (_checking) Padding(padding: const EdgeInsets.all(8), child: Row(mainAxisSize: MainAxisSize.min, children: [const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)), const SizedBox(width: 8), Text(context.l.checkingPin)])),
          const SizedBox(height: 16),
          NumPad(
            onKey: (k) => _pin.length < 6 && !_checking ? setState(() => _pin += k) : null,
            onBackspace: () => _pin.isNotEmpty ? setState(() => _pin = _pin.substring(0, _pin.length - 1)) : null,
            onDone: _pin.length >= 4 && !_checking ? _checkPin : null,
            doneLabel: context.l.confirm,
          ),
        ],
      );
}

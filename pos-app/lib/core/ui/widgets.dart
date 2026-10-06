import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/services.dart';
import '../l10n/gen/app_localizations.dart';

extension L10nX on BuildContext {
  AppLocalizations get l => AppLocalizations.of(this);
}

/// Translated message for a backend / policy reason code.
String reasonText(AppLocalizations l, String? code) => switch (code) {
      'insufficient_funds' => l.reason_insufficient_funds,
      'card_frozen' => l.reason_card_frozen,
      'card_lost' => l.reason_card_lost,
      'per_transaction_cap_exceeded' => l.reason_per_transaction_cap_exceeded,
      'daily_cap_exceeded' => l.reason_daily_cap_exceeded,
      'weekly_cap_exceeded' => l.reason_weekly_cap_exceeded,
      'category_blocked' => l.reason_category_blocked,
      'category_not_allowed' => l.reason_category_not_allowed,
      'item_blocked' => l.reason_item_blocked,
      'merchant_blocked' => l.reason_merchant_blocked,
      'p2p_disabled' => l.reason_p2p_disabled,
      'p2p_cap_exceeded' => l.reason_p2p_cap_exceeded,
      'wallet_not_spendable' => l.reason_wallet_not_spendable,
      'pin_invalid' => l.reason_pin_invalid,
      'unknown_card' => l.reason_unknown_card,
      'card_locked_on_device' => l.reason_card_locked_on_device,
      'recipient_card_inactive' => l.reason_recipient_card_inactive,
      'recipient_not_found' => l.reason_recipient_not_found,
      _ => l.reason_other(code ?? '?'),
    };

String ago(AppLocalizations l, DateTime? t) {
  if (t == null) return l.never;
  final d = DateTime.now().difference(t);
  return d.inHours >= 1 ? l.hoursAgo(d.inHours) : l.minutesAgo(d.inMinutes);
}

/// Online/offline, pending queue, last sync, cache age — on every screen.
class StatusBar extends ConsumerWidget {
  const StatusBar({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final s = ref.watch(statusProvider).value;
    if (s == null) return const SizedBox(height: 28);
    final color = s.online ? Colors.green.shade700 : Colors.orange.shade800;
    final style = Theme.of(context).textTheme.labelSmall;
    return Material(
      color: s.cacheStale ? Colors.amber.shade100 : Theme.of(context).colorScheme.surfaceContainerHighest,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 4),
        child: Wrap(
          spacing: 12,
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Row(mainAxisSize: MainAxisSize.min, children: [
              Icon(s.online ? Icons.wifi : Icons.wifi_off, size: 14, color: color),
              const SizedBox(width: 4),
              Text(s.online ? l.online : l.offline, style: style?.copyWith(color: color, fontWeight: FontWeight.bold)),
            ]),
            Text(l.pendingCount(s.pending), key: const Key('pending-count'), style: style),
            Text(s.syncing ? l.syncing : l.lastSync(ago(l, s.lastSync)), style: style),
            Text(s.cacheStale ? l.cacheStale : l.cacheAge(ago(l, s.cacheRefreshedAt)), style: style),
          ],
        ),
      ),
    );
  }
}

/// Big numeric keypad for PINs and amounts (counter terminals, gloves, rush).
class NumPad extends StatelessWidget {
  const NumPad({super.key, required this.onKey, this.onBackspace, this.onDone, this.doneLabel});
  final void Function(String) onKey;
  final VoidCallback? onBackspace;
  final VoidCallback? onDone;
  final String? doneLabel;

  @override
  Widget build(BuildContext context) {
    Widget key(String label, VoidCallback? onTap, {Widget? child, Key? k}) => Expanded(
          child: Padding(
            padding: const EdgeInsets.all(4),
            child: SizedBox(
              height: 60,
              child: FilledButton.tonal(key: k, onPressed: onTap, child: child ?? Text(label, style: const TextStyle(fontSize: 24))),
            ),
          ),
        );
    Widget row(List<String> ks) => Row(children: [for (final k in ks) key(k, () => onKey(k), k: Key('key-$k'))]);
    return Column(mainAxisSize: MainAxisSize.min, children: [
      row(['1', '2', '3']),
      row(['4', '5', '6']),
      row(['7', '8', '9']),
      Row(children: [
        key('', onBackspace, child: const Icon(Icons.backspace_outlined), k: const Key('key-back')),
        key('0', () => onKey('0'), k: const Key('key-0')),
        key(doneLabel ?? 'OK', onDone, child: Text(doneLabel ?? 'OK'), k: const Key('key-done')),
      ]),
    ]);
  }
}

void showError(BuildContext context, String message) => ScaffoldMessenger.of(context)
  ..clearSnackBars()
  ..showSnackBar(SnackBar(content: Text(message), backgroundColor: Colors.red.shade700));

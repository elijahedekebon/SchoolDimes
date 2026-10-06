import 'package:flutter/material.dart';

import '../../core/api/parent_api.dart';
import '../../core/l10n/gen/app_localizations.dart';
import '../../core/ui/widgets.dart';
import '../disputes/dispute_sheet.dart';

String entryLabel(AppLocalizations l, String type) => switch (type) {
      'pos_purchase' => l.entry_pos_purchase,
      'deposit' => l.entry_deposit,
      'gift_voucher' => l.entry_gift_voucher,
      'refund' => l.entry_refund,
      'fee_payment' => l.entry_fee_payment,
      'p2p_transfer_in' => l.entry_p2p_transfer_in,
      'p2p_transfer_out' => l.entry_p2p_transfer_out,
      'savings_move_in' => l.entry_savings_move_in,
      'savings_move_out' => l.entry_savings_move_out,
      'savings_withdrawal' => l.entry_savings_withdrawal,
      'shortfall_recovery' => l.entry_shortfall_recovery,
      'reversal' => l.entry_reversal,
      _ => l.entry_other,
    };

/// One ledger row; tap for line items and "report a problem".
class TransactionTile extends StatelessWidget {
  const TransactionTile({super.key, required this.txn, this.dense = false, this.studentId, this.onChanged});
  final Json txn;
  final bool dense;
  final int? studentId;
  final VoidCallback? onChanged;

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final debit = txn['direction'] == 'debit';
    final pos = (txn['pos'] as Map?)?.cast<String, dynamic>();
    final items = (pos?['items'] as List?)?.cast<Map>() ?? const [];
    final title = items.isNotEmpty ? items.map((i) => '${i['quantity']}× ${i['description']}').join(', ') : entryLabel(l, txn['entry_type'] as String);
    return ListTile(
      key: Key('txn-${txn['id']}'),
      dense: dense,
      contentPadding: dense ? EdgeInsets.zero : null,
      title: Text(title, maxLines: 1, overflow: TextOverflow.ellipsis),
      subtitle: Text('${shortDate(txn['created_at'] as String?)}${pos != null ? ' · ${pos['merchant_name'] ?? pos['device_name']}' : ''}${txn['open_dispute'] != null ? ' · ${l.disputeOpen}' : ''}'),
      trailing: Text('${debit ? '-' : '+'}${money(txn['amount'])}', style: TextStyle(color: debit ? Colors.red.shade700 : Colors.green.shade700, fontWeight: FontWeight.w600)),
      onTap: () => showModalBottomSheet<void>(
        context: context,
        showDragHandle: true,
        builder: (c) => SafeArea(
          child: ListView(shrinkWrap: true, padding: const EdgeInsets.all(16), children: [
            Text(entryLabel(l, txn['entry_type'] as String), style: Theme.of(c).textTheme.titleLarge),
            Text(shortDate(txn['created_at'] as String?)),
            if (pos != null) Text(pos['merchant_name'] as String? ?? pos['device_name'] as String),
            const Divider(),
            if (items.isNotEmpty) Text(l.items, style: Theme.of(c).textTheme.titleSmall),
            for (final i in items)
              ListTile(dense: true, title: Text('${i['quantity']}× ${i['description']}'), trailing: Text(money(i['line_total']))),
            ListTile(title: Text('${debit ? '-' : '+'}${money(txn['amount'])}', style: Theme.of(c).textTheme.titleMedium)),
            if (txn['dispute_target'] != null && txn['open_dispute'] == null)
              OutlinedButton.icon(
                key: const Key('report-problem'),
                icon: const Icon(Icons.report_problem_outlined),
                label: Text(l.reportProblem),
                onPressed: () async {
                  Navigator.pop(c);
                  final sent = await showDisputeSheet(context, (txn['dispute_target'] as Map).cast<String, dynamic>());
                  if (sent) onChanged?.call();
                },
              ),
            if (txn['open_dispute'] != null) Chip(label: Text(l.disputeOpen)),
          ]),
        ),
      ),
    );
  }
}

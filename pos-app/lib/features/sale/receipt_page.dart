import 'package:flutter/material.dart';

import '../../core/money/money.dart';
import '../../core/ui/widgets.dart';
import 'sale_screen.dart';
import 'sale_service.dart';

class ReceiptPage extends StatelessWidget {
  const ReceiptPage({super.key, required this.lines, required this.total, required this.studentName, required this.outcome});
  final List<CartLine> lines;
  final Money total;
  final String studentName;
  final SaleOutcome outcome;

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final offline = outcome.channel == SaleChannel.offline;
    final theme = Theme.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l.receiptTitle), automaticallyImplyLeading: false),
      body: Column(children: [
        const StatusBar(),
        Expanded(
          child: ListView(padding: const EdgeInsets.all(16), children: [
            Icon(Icons.check_circle, size: 72, color: Colors.green.shade600),
            const SizedBox(height: 8),
            Text(studentName, textAlign: TextAlign.center, style: theme.textTheme.headlineSmall),
            if (offline)
              Center(child: Padding(padding: const EdgeInsets.all(8), child: Chip(key: const Key('offline-badge'), avatar: const Icon(Icons.cloud_off, size: 18), label: Text(l.offlineWillSync)))),
            if (outcome.flags.isNotEmpty)
              Center(child: Chip(label: Text(l.flaggedForReview), backgroundColor: Colors.orange.shade100)),
            const Divider(),
            for (final line in lines)
              ListTile(dense: true, title: Text(line.description), subtitle: Text('${line.quantity} × ${line.unitPrice.format()}'), trailing: Text(line.total.format())),
            const Divider(),
            ListTile(title: Text(l.total, style: theme.textTheme.titleLarge), trailing: Text(total.format(), style: theme.textTheme.titleLarge)),
            if (outcome.newBalance != null)
              ListTile(
                title: Text(l.newBalance),
                subtitle: offline ? Text(l.estimated) : null,
                trailing: Text(outcome.newBalance!.format(), key: const Key('receipt-balance'), style: theme.textTheme.titleMedium),
              ),
            const SizedBox(height: 8),
            Text(l.voidHint, style: theme.textTheme.bodySmall, textAlign: TextAlign.center),
          ]),
        ),
        Padding(
          padding: const EdgeInsets.all(16),
          child: SizedBox(width: double.infinity, height: 56, child: FilledButton(key: const Key('receipt-done'), onPressed: () => Navigator.pop(context), child: Text(l.done))),
        ),
      ]),
    );
  }
}

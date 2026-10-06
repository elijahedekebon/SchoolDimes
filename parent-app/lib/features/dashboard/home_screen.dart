import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/ui/widgets.dart';
import '../child/child_screen.dart';
import '../child/transaction_tile.dart';
import '../topup/topup_screen.dart';

class HomeScreen extends ConsumerWidget {
  const HomeScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final dash = ref.watch(dashboardProvider);
    final email = ref.watch(authProvider).value?.me?['email'] as String? ?? '';
    return AsyncBody<DashboardState>(
      value: AsyncSnapshotLike(dash.value, dash.hasError && !dash.hasValue ? dash.error : null),
      onRetry: () => ref.read(dashboardProvider.notifier).refresh(),
      data: (d) => RefreshIndicator(
        onRefresh: () => ref.read(dashboardProvider.notifier).refresh(),
        child: ListView(padding: const EdgeInsets.all(12), children: [
          if (d.offlineSince != null)
            Card(
              key: const Key('offline-banner'),
              color: Colors.amber.shade100,
              child: ListTile(leading: const Icon(Icons.cloud_off), title: Text(l.lastUpdated(shortDate(d.offlineSince!.toIso8601String())))),
            ),
          if (d.students.isEmpty) Padding(padding: const EdgeInsets.all(24), child: Text(l.noChildren(email), textAlign: TextAlign.center)),
          for (final s in d.students) ChildCard(student: s, readOnly: d.offlineSince != null),
          if (d.tip != null)
            Card(
              color: Colors.purple.shade50,
              child: ListTile(leading: const Icon(Icons.lightbulb_outline), title: Text(d.tip!['title'] as String), subtitle: Text(d.tip!['body'] as String)),
            ),
        ]),
      ),
    );
  }
}

class ChildCard extends ConsumerWidget {
  const ChildCard({super.key, required this.student, this.readOnly = false});
  final Json student;
  final bool readOnly;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final theme = Theme.of(context);
    final card = (student['card'] as Map?)?.cast<String, dynamic>();
    final status = card?['status'] as String?;
    final goals = (student['savings_goals'] as List).cast<Map>();
    final recent = (student['recent_transactions'] as List).cast<Map>();
    final name = student['first_name'] as String;
    return Card(
      key: Key('child-${student['id']}'),
      margin: const EdgeInsets.only(bottom: 12),
      child: InkWell(
        onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => ChildScreen(student: student))),
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            Row(children: [
              CircleAvatar(child: Text(name.characters.first)),
              const SizedBox(width: 12),
              Expanded(child: Text('${student['name']} · ${student['class_name']}', style: theme.textTheme.titleMedium)),
              _CardChip(status: status),
            ]),
            const SizedBox(height: 12),
            Row(children: [
              Expanded(child: _Balance(label: l.mainBalance, value: money(student['main_wallet']?['balance']), warn: student['is_low_balance'] == true, k: 'balance-${student['id']}')),
              Expanded(child: _Balance(label: l.savingsBalance, value: money(student['savings_wallet']?['balance']))),
            ]),
            for (final g in goals.take(1)) ...[
              const SizedBox(height: 8),
              Text('${g['goal_name']}  ${money(g['current_amount'])} / ${money(g['target_amount'])}', style: theme.textTheme.bodySmall),
              LinearProgressIndicator(value: ((g['progress_percent'] as num?) ?? 0) / 100, color: g['is_reached'] == true ? Colors.green : null),
            ],
            if (recent.isNotEmpty) ...[
              const Divider(),
              Text(l.recentPurchases, style: theme.textTheme.labelLarge),
              for (final t in recent.take(3)) TransactionTile(txn: t.cast<String, dynamic>(), dense: true),
            ],
            if (!readOnly)
              Row(mainAxisAlignment: MainAxisAlignment.end, children: [
                if (card != null && status != 'lost')
                  TextButton.icon(
                    key: Key('freeze-${student['id']}'),
                    icon: Icon(status == 'frozen' ? Icons.lock_open : Icons.ac_unit),
                    label: Text(status == 'frozen' ? l.unfreeze : l.freeze),
                    onPressed: () => toggleFreeze(context, ref, student),
                  ),
                FilledButton.icon(
                  key: Key('topup-${student['id']}'),
                  icon: const Icon(Icons.add),
                  label: Text(l.topUp),
                  onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => TopUpScreen(initialWalletId: student['main_wallet']['id'] as int))),
                ),
              ]),
          ]),
        ),
      ),
    );
  }
}

/// Freeze/unfreeze in two taps (button + confirm), from anywhere.
Future<void> toggleFreeze(BuildContext context, WidgetRef ref, Json student) async {
  final l = context.l;
  final card = (student['card'] as Map).cast<String, dynamic>();
  final frozen = card['status'] == 'frozen';
  final name = student['first_name'] as String;
  if (!await confirmDialog(context, frozen ? l.unfreezeConfirm(name) : l.freezeConfirm(name), danger: !frozen)) return;
  if (!context.mounted) return;
  final api = ref.read(parentApiProvider);
  final r = await guarded(context, () => frozen ? api.unfreezeCard(card['id'] as int) : api.freezeCard(card['id'] as int));
  if (r != null) await ref.read(dashboardProvider.notifier).refresh();
}

class _Balance extends StatelessWidget {
  const _Balance({required this.label, required this.value, this.warn = false, this.k});
  final String label, value;
  final bool warn;
  final String? k;
  @override
  Widget build(BuildContext context) => Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
        Text(label, style: Theme.of(context).textTheme.labelMedium),
        Text(value, key: k == null ? null : Key(k!), style: Theme.of(context).textTheme.headlineSmall?.copyWith(color: warn ? Colors.orange.shade800 : null)),
        if (warn) Text(context.l.lowBalance, style: TextStyle(color: Colors.orange.shade800, fontSize: 12)),
      ]);
}

class _CardChip extends StatelessWidget {
  const _CardChip({required this.status});
  final String? status;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final (text, color) = switch (status) {
      'active' => (l.card_active, Colors.green),
      'frozen' => (l.card_frozen, Colors.cyan.shade700),
      'lost' => (l.card_lost, Colors.red),
      _ => (l.card_none, Colors.grey),
    };
    return Chip(label: Text(text, key: const Key('card-status')), side: BorderSide(color: color), labelStyle: TextStyle(color: color));
  }
}

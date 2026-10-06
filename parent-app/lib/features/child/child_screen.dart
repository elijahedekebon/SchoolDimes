import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:uuid/uuid.dart';

import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/money/money.dart';
import '../../core/ui/widgets.dart';
import '../dashboard/home_screen.dart';
import 'transaction_tile.dart';

enum ChildTab { history, limits, savings, card }

class ChildScreen extends ConsumerWidget {
  const ChildScreen({super.key, required this.student, this.initialTab = ChildTab.history});
  final Json student;
  final ChildTab initialTab;

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    // always show the freshest copy from the dashboard
    final live = ref.watch(dashboardProvider).value?.students.where((s) => s['id'] == student['id']).firstOrNull ?? student;
    return DefaultTabController(
      length: 4,
      initialIndex: initialTab.index,
      child: Scaffold(
        appBar: AppBar(
          title: Text(live['name'] as String),
          bottom: TabBar(isScrollable: true, tabs: [Tab(text: l.history), Tab(text: l.controls), Tab(text: l.savings), Tab(text: l.cardAndP2p)]),
        ),
        body: TabBarView(children: [_History(student: live), _Limits(student: live), _Savings(student: live), _CardP2P(student: live)]),
      ),
    );
  }
}

class _History extends ConsumerStatefulWidget {
  const _History({required this.student});
  final Json student;
  @override
  ConsumerState<_History> createState() => _HistoryState();
}

class _HistoryState extends ConsumerState<_History> {
  String _type = '';
  DateTimeRange? _range;
  int _gen = 0;

  Map<String, dynamic> get _filters => {
        if (_type == 'purchases') 'entry_type': 'pos_purchase',
        if (_type == 'topups') 'entry_type': 'deposit,gift_voucher,refund',
        if (_type == 'other') 'entry_type': 'fee_payment,p2p_transfer_in,p2p_transfer_out,savings_move_in,savings_move_out,savings_withdrawal,shortfall_recovery',
        if (_range != null) 'from': _range!.start.toIso8601String().substring(0, 10),
        if (_range != null) 'to': _range!.end.toIso8601String().substring(0, 10),
      };

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final id = widget.student['id'] as int;
    return Column(children: [
      SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        padding: const EdgeInsets.all(8),
        child: Row(children: [
          for (final (k, label) in [('', l.filterAll), ('purchases', l.filterPurchases), ('topups', l.filterTopUps), ('other', l.filterOther)])
            Padding(padding: const EdgeInsets.only(right: 6), child: ChoiceChip(label: Text(label), selected: _type == k, onSelected: (_) => setState(() => _type = k))),
          ActionChip(
            avatar: const Icon(Icons.date_range, size: 18),
            label: Text(_range == null ? '${l.from}–${l.to}' : '${_range!.start.toIso8601String().substring(0, 10)} – ${_range!.end.toIso8601String().substring(0, 10)}'),
            onPressed: () async {
              final r = await showDateRangePicker(context: context, firstDate: DateTime(2024), lastDate: DateTime.now().add(const Duration(days: 1)));
              setState(() => _range = r);
            },
          ),
        ]),
      ),
      Expanded(
        child: Loader<Json>(
          key: ValueKey('$_type$_range$_gen'),
          load: () => ref.read(parentApiProvider).transactions(id, filters: _filters),
          builder: (c, page, reload) {
            final rows = (page['results'] as List).cast<Map>();
            if (rows.isEmpty) return ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingYet))]);
            return ListView(children: [
              for (final t in rows) TransactionTile(txn: t.cast<String, dynamic>(), studentId: id, onChanged: () => setState(() => _gen++)),
            ]);
          },
        ),
      ),
    ]);
  }
}

class _Limits extends ConsumerStatefulWidget {
  const _Limits({required this.student});
  final Json student;
  @override
  ConsumerState<_Limits> createState() => _LimitsState();
}

class _LimitsState extends ConsumerState<_Limits> {
  final _ctl = <String, TextEditingController>{};
  bool? _p2p;
  int _gen = 0;

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final id = widget.student['id'] as int;
    final api = ref.read(parentApiProvider);
    return Loader<Json>(
      key: ValueKey(_gen),
      load: () => api.spendingControls(id),
      builder: (c, sc, reload) {
        final school = (sc['school_default'] as Map).cast<String, dynamic>();
        final ov = (sc['override'] as Map?)?.cast<String, dynamic>();
        String schoolValue(String f) => school[f] == null ? l.noLimit : money(school[f]);
        final fields = {'daily_spend_cap': l.dailyCap, 'weekly_spend_cap': l.weeklyCap, 'per_transaction_cap': l.perTxnCap, 'p2p_daily_cap': l.p2pCap};
        for (final f in fields.keys) {
          _ctl.putIfAbsent(f, () => TextEditingController(text: ov?[f] == null ? '' : Money.parse(ov![f] as String).toApi().replaceAll('.00', '')));
        }
        _p2p ??= ov?['p2p_enabled'] != false && school['p2p_enabled'] != false;
        return ListView(padding: const EdgeInsets.all(16), children: [
          Text(l.controlsHelp, style: Theme.of(context).textTheme.bodySmall),
          for (final e in fields.entries)
            TextField(
              key: Key('limit-${e.key}'),
              controller: _ctl[e.key],
              keyboardType: const TextInputType.numberWithOptions(decimal: true),
              decoration: InputDecoration(labelText: e.value, prefixText: 'UGX ', helperText: l.schoolLimit(schoolValue(e.key))),
            ),
          SwitchListTile(
            title: Text(l.p2pEnabled),
            subtitle: school['p2p_enabled'] == false ? Text(l.schoolLimit(l.noLimit)) : null,
            value: _p2p!,
            // tighten only: can't turn on what the school turned off
            onChanged: school['p2p_enabled'] == false ? null : (v) => setState(() => _p2p = v),
          ),
          const SizedBox(height: 12),
          FilledButton(
            key: const Key('limits-save'),
            onPressed: () async {
              final body = <String, dynamic>{'p2p_enabled': _p2p == false ? false : null};
              for (final f in fields.keys) {
                final m = Money.tryParse(_ctl[f]!.text);
                body[f] = m?.toApi();
              }
              // the backend refuses anything looser than the school's limits (policy_cannot_loosen)
              final r = await guarded(context, () => ov == null ? api.createOverride({...body, 'student': id}) : api.updateOverride(ov['id'] as int, body), success: l.saved);
              if (r != null) setState(() => _gen++);
            },
            child: Text(l.save),
          ),
          const Divider(height: 32),
          _LowBalanceAlert(studentId: id),
        ]);
      },
    );
  }
}

class _LowBalanceAlert extends ConsumerWidget {
  const _LowBalanceAlert({required this.studentId});
  final int studentId;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final api = ref.read(parentApiProvider);
    final ctl = TextEditingController();
    return Loader<Json>(
      load: api.preferences,
      builder: (c, prefs, _) {
        final v = ((prefs['low_balance_thresholds'] as Map?) ?? {})['$studentId'];
        if (v != null && ctl.text.isEmpty) ctl.text = Money.parse(v.toString()).toApi().replaceAll('.00', '');
        return Row(children: [
          Expanded(child: TextField(controller: ctl, decoration: InputDecoration(labelText: c.l.lowBalanceAlert, prefixText: 'UGX '), keyboardType: TextInputType.number)),
          IconButton(
            icon: const Icon(Icons.check),
            onPressed: () {
              final m = Money.tryParse(ctl.text);
              final all = Map<String, dynamic>.from((prefs['low_balance_thresholds'] as Map?) ?? {});
              if (m == null) {
                all.remove('$studentId');
              } else {
                all['$studentId'] = m.toApi();
              }
              guarded(context, () => api.updatePreferences({'low_balance_thresholds': all}), success: c.l.saved);
            },
          ),
        ]);
      },
    );
  }
}

class _Savings extends ConsumerStatefulWidget {
  const _Savings({required this.student});
  final Json student;
  @override
  ConsumerState<_Savings> createState() => _SavingsState();
}

class _SavingsState extends ConsumerState<_Savings> {
  final _amount = TextEditingController();
  int _gen = 0;
  String? _withdrawKey; // kept across retries of one withdrawal; new after success

  Future<void> _refresh() async {
    setState(() => _gen++);
    await ref.read(dashboardProvider.notifier).refresh();
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final s = widget.student;
    final api = ref.read(parentApiProvider);
    final mainId = s['main_wallet']['id'] as int, savings = (s['savings_wallet'] as Map).cast<String, dynamic>();
    final open = savings['withdrawal_window_open'] == true;
    return ListView(key: ValueKey(_gen), padding: const EdgeInsets.all(16), children: [
      Row(children: [
        Expanded(child: ListTile(title: Text(l.mainBalance), subtitle: Text(money(s['main_wallet']['balance'])))),
        Expanded(child: ListTile(title: Text(l.savingsBalance), subtitle: Text(money(savings['balance'])))),
      ]),
      TextField(controller: _amount, decoration: InputDecoration(labelText: l.amount, prefixText: 'UGX '), keyboardType: TextInputType.number),
      Row(children: [
        Expanded(child: OutlinedButton(onPressed: () => _move(api.moveToSavings(mainId, _amountApi)), child: Text(l.moveIn))),
        const SizedBox(width: 8),
        Expanded(child: OutlinedButton(onPressed: () => _move(api.moveFromSavings(mainId, _amountApi)), child: Text(l.moveOut))),
      ]),
      const Divider(height: 32),
      Row(children: [Text(l.goals, style: Theme.of(context).textTheme.titleMedium), const Spacer(), TextButton.icon(onPressed: () => _newGoal(savings['id'] as int), icon: const Icon(Icons.add), label: Text(l.newGoal))]),
      for (final g in (s['savings_goals'] as List).cast<Map>())
        ListTile(
          title: Text('${g['goal_name']}${g['is_reached'] == true ? '  🎉' : ''}'),
          subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
            LinearProgressIndicator(value: ((g['progress_percent'] as num?) ?? 0) / 100, minHeight: 8, color: g['is_reached'] == true ? Colors.green : null),
            Text('${money(g['current_amount'])} / ${money(g['target_amount'])}${g['is_reached'] == true ? ' · ${l.goalReached}' : ''}'),
          ]),
          trailing: IconButton(icon: const Icon(Icons.delete_outline), onPressed: () async {
            if (await guarded(context, () => api.deleteGoal(g['id'] as int).then((_) => true)) == true) await _refresh();
          }),
        ),
      const Divider(height: 32),
      Text(l.withdrawWindow, style: Theme.of(context).textTheme.titleMedium),
      Text(l.withdrawWindowHelp, style: Theme.of(context).textTheme.bodySmall),
      ListTile(
        title: Text(open ? l.windowOpen(shortDate(savings['withdrawal_window_end'] as String?)) : l.windowClosed),
        trailing: TextButton(onPressed: () => _setWindow(savings['id'] as int), child: Text(l.setWindow)),
      ),
      FilledButton.tonal(onPressed: open ? () => _withdraw(savings['id'] as int) : null, child: Text(l.withdraw)),
      const SizedBox(height: 16),
      Text(l.payoutStatus, style: Theme.of(context).textTheme.titleSmall),
      Loader<List<Json>>(
        key: ValueKey('payouts$_gen'),
        load: () => api.payouts(s['id'] as int),
        builder: (c, rows, _) => Column(children: [
          if (rows.isEmpty) Text(l.nothingYet),
          for (final p in rows)
            ListTile(
              dense: true,
              title: Text('${money(p['amount'])} → ${p['phone_number']}'),
              subtitle: Text(shortDate(p['created_at'] as String?)),
              trailing: Text(switch (p['status']) { 'succeeded' => l.payout_succeeded, 'failed' => l.payout_failed, _ => l.payout_pending }),
            ),
        ]),
      ),
    ]);
  }

  String get _amountApi => (Money.tryParse(_amount.text) ?? const Money.zero()).toApi();

  Future<void> _move(Future<Json> call) async {
    if (await guarded(context, () => call, success: context.l.saved) != null) {
      _amount.clear();
      await _refresh();
    }
  }

  Future<void> _newGoal(int savingsWalletId) async {
    final l = context.l;
    final name = TextEditingController(), target = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.newGoal),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: name, decoration: InputDecoration(labelText: l.goalName)),
          TextField(controller: target, decoration: InputDecoration(labelText: l.goalTarget, prefixText: 'UGX '), keyboardType: TextInputType.number),
        ]),
        actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.save))],
      ),
    );
    final m = Money.tryParse(target.text);
    if (ok == true && m != null && mounted) {
      if (await guarded(context, () => ref.read(parentApiProvider).createGoal({'wallet': savingsWalletId, 'goal_name': name.text.trim(), 'target_amount': m.toApi()})) != null) await _refresh();
    }
  }

  Future<void> _setWindow(int savingsWalletId) async {
    final r = await showDateRangePicker(context: context, firstDate: DateTime.now().subtract(const Duration(days: 1)), lastDate: DateTime.now().add(const Duration(days: 365)));
    if (r == null || !mounted) return;
    final body = {'withdrawal_window_start': r.start.toUtc().toIso8601String(), 'withdrawal_window_end': r.end.add(const Duration(days: 1)).toUtc().toIso8601String()};
    if (await guarded(context, () => ref.read(parentApiProvider).setWithdrawalWindow(savingsWalletId, body), success: context.l.saved) != null) await _refresh();
  }

  Future<void> _withdraw(int savingsWalletId) async {
    final m = Money.tryParse(_amount.text);
    if (m == null || !m.isPositive) {
      showMessage(context, context.l.amountInvalid, error: true);
      return;
    }
    _withdrawKey ??= const Uuid().v4();
    final r = await guarded(context, () => ref.read(parentApiProvider).withdraw(savingsWalletId, {'amount': m.toApi(), 'idempotency_key': _withdrawKey}));
    if (r != null) {
      _withdrawKey = null;
      await _refresh();
    }
  }
}

class _CardP2P extends ConsumerWidget {
  const _CardP2P({required this.student});
  final Json student;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final card = (student['card'] as Map?)?.cast<String, dynamic>();
    final id = student['id'] as int;
    return ListView(padding: const EdgeInsets.all(16), children: [
      if (card != null) ...[
        ListTile(leading: const Icon(Icons.credit_card), title: Text(switch (card['status']) { 'frozen' => l.card_frozen, 'lost' => l.card_lost, _ => l.card_active })),
        if (card['status'] != 'lost')
          Row(children: [
            Expanded(child: FilledButton.tonal(key: const Key('child-freeze'), onPressed: () => toggleFreeze(context, ref, student), child: Text(card['status'] == 'frozen' ? l.unfreeze : l.freeze))),
            const SizedBox(width: 8),
            Expanded(
              child: OutlinedButton(
                onPressed: () async {
                  if (!await confirmDialog(context, l.reportLostConfirm(student['first_name'] as String), danger: true) || !context.mounted) return;
                  if (await guarded(context, () => ref.read(parentApiProvider).reportLost(card['id'] as int)) != null) await ref.read(dashboardProvider.notifier).refresh();
                },
                child: Text(l.reportLost),
              ),
            ),
          ]),
      ] else
        ListTile(title: Text(l.card_none)),
      const Divider(height: 32),
      Text(l.p2pHistory, style: Theme.of(context).textTheme.titleMedium),
      Loader<Json>(
        load: () => ref.read(parentApiProvider).p2pHistory(id),
        builder: (c, page, _) {
          final rows = (page['results'] as List).cast<Map>();
          return Column(children: [
            if (rows.isEmpty) Padding(padding: const EdgeInsets.all(8), child: Text(l.nothingYet)),
            for (final p in rows)
              ListTile(
                dense: true,
                title: Text(p['sender_student'] == id ? l.p2pSent(p['recipient_name'] as String) : l.p2pReceived(p['sender_name'] as String)),
                subtitle: Text('${shortDate(p['created_at'] as String?)}${(p['note'] as String?)?.isNotEmpty == true ? ' · ${p['note']}' : ''}'),
                trailing: Text(money(p['amount'])),
              ),
          ]);
        },
      ),
    ]);
  }
}

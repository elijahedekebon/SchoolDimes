import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';
import 'package:uuid/uuid.dart';

import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/money/money.dart';
import '../../core/ui/widgets.dart';
import '../topup/topup_screen.dart';

class PaymentsScreen extends StatelessWidget {
  const PaymentsScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    Widget item(IconData i, String t, Widget page) => ListTile(
        leading: Icon(i), title: Text(t), trailing: const Icon(Icons.chevron_right), onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => page)));
    return ListView(children: [
      item(Icons.add_card, l.topUp, const TopUpScreen()),
      item(Icons.event_repeat, l.recurringTitle, const RecurringScreen()),
      item(Icons.card_giftcard, l.giftsTitle, const GiftsScreen()),
      item(Icons.groups, l.fundsTitle, const FundsScreen()),
      item(Icons.receipt_long, l.depositHistory, const DepositHistoryScreen()),
      item(Icons.volunteer_activism, l.contributionsReceived, const DepositHistoryScreen(fromContributors: true)),
    ]);
  }
}

// ---------------------------------------------------------------- recurring

class RecurringScreen extends ConsumerStatefulWidget {
  const RecurringScreen({super.key});
  @override
  ConsumerState<RecurringScreen> createState() => _RecurringScreenState();
}

class _RecurringScreenState extends ConsumerState<RecurringScreen> {
  int _gen = 0;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    final students = ref.watch(dashboardProvider).value?.students ?? const <Json>[];
    String nameOf(int sid) => students.where((s) => s['id'] == sid).map((s) => s['name'] as String).firstOrNull ?? '#$sid';
    String weekday(int d) => [l.weekday0, l.weekday1, l.weekday2, l.weekday3, l.weekday4, l.weekday5, l.weekday6][d];
    return Scaffold(
      appBar: AppBar(title: Text(l.recurringTitle)),
      floatingActionButton: FloatingActionButton.extended(onPressed: () => _edit(null, students), icon: const Icon(Icons.add), label: Text(l.recurringAdd)),
      body: Loader<List<Json>>(
        key: ValueKey(_gen),
        load: api.recurring,
        builder: (c, rows, _) => ListView(children: [
          if (rows.isEmpty) Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingYet)),
          for (final r in rows)
            ListTile(
              title: Text('${money(r['amount'])} → ${nameOf(r['student'] as int)}'),
              subtitle: Text([
                r['frequency'] == 'weekly' ? '${l.weekly} · ${weekday(r['day_of_week'] as int)}' : '${l.monthly} · ${r['day_of_month']}',
                if (r['active'] == true) l.nextRun(shortDate(r['next_run_at'] as String?)),
                if (r['active'] != true) (r['consecutive_failures'] as int? ?? 0) > 0 ? l.autoPaused(r['consecutive_failures'] as int) : l.paused,
                if ((r['last_status'] as String?)?.isNotEmpty == true) l.lastStatus(r['last_status'] as String),
              ].join('\n')),
              isThreeLine: true,
              trailing: PopupMenuButton<String>(
                onSelected: (a) async {
                  Json? ok;
                  if (a == 'toggle') {
                    ok = await guarded(context, () => api.updateRecurring(r['id'] as int, {'active': r['active'] != true}));
                  } else if (await confirmDialog(context, '${l.delete}?', danger: true) && context.mounted) {
                    ok = await guarded(context, () => api.deleteRecurring(r['id'] as int).then((_) => <String, dynamic>{}));
                  }
                  if (ok != null) setState(() => _gen++);
                },
                itemBuilder: (_) => [
                  PopupMenuItem(value: 'toggle', child: Text(r['active'] == true ? l.pause : l.resume)),
                  PopupMenuItem(value: 'delete', child: Text(l.delete)),
                ],
              ),
            ),
        ]),
      ),
    );
  }

  Future<void> _edit(Json? existing, List<Json> students) async {
    final l = context.l;
    int? student = students.firstOrNull?['id'] as int?;
    final amount = TextEditingController();
    String freq = 'weekly';
    int dow = 0, dom = 1;
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => StatefulBuilder(
        builder: (c, set) => AlertDialog(
          title: Text(l.recurringAdd),
          content: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              DropdownButtonFormField<int>(initialValue: student, decoration: InputDecoration(labelText: l.child), items: [for (final s in students) DropdownMenuItem(value: s['id'] as int, child: Text(s['name'] as String))], onChanged: (v) => set(() => student = v)),
              TextField(controller: amount, decoration: InputDecoration(labelText: l.amount, prefixText: 'UGX '), keyboardType: TextInputType.number),
              DropdownButtonFormField<String>(initialValue: freq, decoration: InputDecoration(labelText: l.frequency), items: [DropdownMenuItem(value: 'weekly', child: Text(l.weekly)), DropdownMenuItem(value: 'monthly', child: Text(l.monthly))], onChanged: (v) => set(() => freq = v ?? 'weekly')),
              if (freq == 'weekly')
                DropdownButtonFormField<int>(initialValue: dow, decoration: InputDecoration(labelText: l.dayOfWeek), items: [for (var d = 0; d < 7; d++) DropdownMenuItem(value: d, child: Text([l.weekday0, l.weekday1, l.weekday2, l.weekday3, l.weekday4, l.weekday5, l.weekday6][d]))], onChanged: (v) => set(() => dow = v ?? 0))
              else
                DropdownButtonFormField<int>(initialValue: dom, decoration: InputDecoration(labelText: l.dayOfMonth), items: [for (var d = 1; d <= 28; d++) DropdownMenuItem(value: d, child: Text('$d'))], onChanged: (v) => set(() => dom = v ?? 1)),
            ]),
          ),
          actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.save))],
        ),
      ),
    );
    final m = Money.tryParse(amount.text);
    if (ok != true || m == null || student == null || !mounted) return;
    final r = await guarded(context, () => ref.read(parentApiProvider).createRecurring({
          'student': student,
          'amount': m.toApi(),
          'channel': 'momo',
          'frequency': freq,
          'day_of_week': freq == 'weekly' ? dow : null,
          'day_of_month': freq == 'monthly' ? dom : null,
          'active': true,
        }));
    if (r != null) setState(() => _gen++);
  }
}

// -------------------------------------------------------- gifts & links

class GiftsScreen extends ConsumerStatefulWidget {
  const GiftsScreen({super.key});
  @override
  ConsumerState<GiftsScreen> createState() => _GiftsScreenState();
}

class _GiftsScreenState extends ConsumerState<GiftsScreen> {
  int _gen = 0;
  String? _giftKey;

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    final students = ref.watch(dashboardProvider).value?.students ?? const <Json>[];
    return Scaffold(
      appBar: AppBar(title: Text(l.giftsTitle)),
      body: ListView(key: ValueKey(_gen), padding: const EdgeInsets.all(16), children: [
        FilledButton.icon(onPressed: () => _sendGift(students), icon: const Icon(Icons.card_giftcard), label: Text(l.sendGift)),
        const Divider(height: 32),
        Text(l.familyLinks, style: Theme.of(context).textTheme.titleMedium),
        Text(l.familyLinksHelp, style: Theme.of(context).textTheme.bodySmall),
        for (final s in students)
          TextButton.icon(
            icon: const Icon(Icons.link),
            label: Text(l.createLink(s['first_name'] as String)),
            onPressed: () async {
              final link = await guarded(context, () => api.createLink(s['id'] as int));
              if (link != null) {
                setState(() => _gen++);
                await SharePlus.instance.share(ShareParams(text: l.shareText(s['first_name'] as String, link['share_url'] as String)));
              }
            },
          ),
        Loader<List<Json>>(
          load: api.links,
          builder: (c, links, _) => Column(children: [
            for (final k in links)
              ListTile(
                leading: Icon(Icons.link, color: k['active'] == true ? null : Colors.grey),
                title: Text(students.where((s) => s['id'] == k['student']).map((s) => s['first_name'] as String).firstOrNull ?? '#${k['student']}'),
                subtitle: Text(k['active'] == true ? (k['share_url'] as String) : l.linkOff, maxLines: 1, overflow: TextOverflow.ellipsis),
                trailing: k['active'] != true
                    ? null
                    : Row(mainAxisSize: MainAxisSize.min, children: [
                        IconButton(tooltip: l.share, icon: const Icon(Icons.share), onPressed: () => SharePlus.instance.share(ShareParams(text: k['share_url'] as String))),
                        IconButton(
                          tooltip: l.revoke,
                          icon: const Icon(Icons.link_off),
                          onPressed: () async {
                            if (await confirmDialog(context, l.revokeConfirm, danger: true) && context.mounted) {
                              if (await guarded(context, () => api.revokeLink(k['id'] as int)) != null) setState(() => _gen++);
                            }
                          },
                        ),
                      ]),
              ),
          ]),
        ),
      ]),
    );
  }

  Future<void> _sendGift(List<Json> students) async {
    final l = context.l;
    int? student = students.firstOrNull?['id'] as int?;
    final amount = TextEditingController(), message = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => StatefulBuilder(
        builder: (c, set) => AlertDialog(
          title: Text(l.sendGift),
          content: Column(mainAxisSize: MainAxisSize.min, children: [
            DropdownButtonFormField<int>(initialValue: student, decoration: InputDecoration(labelText: l.child), items: [for (final s in students) DropdownMenuItem(value: s['id'] as int, child: Text(s['name'] as String))], onChanged: (v) => set(() => student = v)),
            TextField(controller: amount, decoration: InputDecoration(labelText: l.amount, prefixText: 'UGX '), keyboardType: TextInputType.number),
            TextField(controller: message, decoration: InputDecoration(labelText: l.giftMessage), maxLength: 280),
          ]),
          actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.confirm))],
        ),
      ),
    );
    final m = Money.tryParse(amount.text);
    if (ok != true || m == null || student == null || !mounted) return;
    _giftKey ??= const Uuid().v4();
    final g = await guarded(context, () => ref.read(parentApiProvider).createGift({'student': student, 'amount': m.toApi(), 'message': message.text.trim(), 'channel': 'momo', 'idempotency_key': _giftKey}));
    if (g != null && mounted) {
      _giftKey = null;
      final dep = {...g, 'id': g['deposit'], 'reference': g['deposit_reference'], 'status': g['deposit_status'] ?? 'pending'};
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => DepositStatusScreen(deposit: dep)));
    }
  }
}

// ------------------------------------------------------------ pooled funds

class FundsScreen extends ConsumerStatefulWidget {
  const FundsScreen({super.key});
  @override
  ConsumerState<FundsScreen> createState() => _FundsScreenState();
}

class _FundsScreenState extends ConsumerState<FundsScreen> {
  int _gen = 0;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.fundsTitle)),
      floatingActionButton: FloatingActionButton.extended(onPressed: _create, icon: const Icon(Icons.add), label: Text(l.createFund)),
      body: Loader<List<Json>>(
        key: ValueKey(_gen),
        load: api.funds,
        builder: (c, rows, _) => ListView(children: [
          if (rows.isEmpty) Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingYet)),
          for (final f in rows)
            ListTile(
              title: Text(f['title'] as String),
              subtitle: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(f['target_amount'] == null ? money(f['total_contributed']) : l.fundRaised(money(f['total_contributed']), money(f['target_amount']))),
                if (f['progress_percent'] != null) LinearProgressIndicator(value: (f['progress_percent'] as num) / 100),
              ]),
              trailing: Text(f['status'] as String),
              onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => FundDetailScreen(id: f['id'] as int))),
            ),
        ]),
      ),
    );
  }

  Future<void> _create() async {
    final l = context.l;
    final title = TextEditingController(), purpose = TextEditingController(), target = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.createFund),
        content: Column(mainAxisSize: MainAxisSize.min, children: [
          TextField(controller: title, decoration: InputDecoration(labelText: l.fundTitle)),
          TextField(controller: purpose, decoration: InputDecoration(labelText: l.fundPurpose)),
          TextField(controller: target, decoration: InputDecoration(labelText: l.fundTarget, prefixText: 'UGX '), keyboardType: TextInputType.number),
        ]),
        actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.save))],
      ),
    );
    if (ok != true || !mounted) return;
    final r = await guarded(context, () => ref.read(parentApiProvider).createFund({'title': title.text.trim(), 'purpose': purpose.text.trim(), 'target_amount': Money.tryParse(target.text)?.toApi()}));
    if (r != null) setState(() => _gen++);
  }
}

class FundDetailScreen extends ConsumerStatefulWidget {
  const FundDetailScreen({super.key, required this.id});
  final int id;
  @override
  ConsumerState<FundDetailScreen> createState() => _FundDetailScreenState();
}

class _FundDetailScreenState extends ConsumerState<FundDetailScreen> {
  String? _key;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.fundsTitle)),
      body: Loader<Json>(
        load: () => api.fund(widget.id),
        builder: (c, f, _) => ListView(padding: const EdgeInsets.all(16), children: [
          Text(f['title'] as String, style: Theme.of(context).textTheme.headlineSmall),
          Text(f['purpose'] as String? ?? ''),
          const SizedBox(height: 8),
          Text(f['target_amount'] == null ? money(f['total_contributed']) : l.fundRaised(money(f['total_contributed']), money(f['target_amount']))),
          if (f['progress_percent'] != null) LinearProgressIndicator(value: (f['progress_percent'] as num) / 100, minHeight: 8),
          const SizedBox(height: 12),
          if (f['status'] == 'open') FilledButton(onPressed: () => _contribute(), child: Text(l.contribute)),
          const Divider(height: 32),
          Text(l.contributions, style: Theme.of(context).textTheme.titleMedium),
          for (final x in ((f['contributions'] as List?) ?? const []).cast<Map>())
            ListTile(dense: true, title: Text(x['contributor_name'] as String? ?? ''), subtitle: Text(shortDate(x['created_at'] as String?)), trailing: Text(money(x['amount']))),
        ]),
      ),
    );
  }

  Future<void> _contribute() async {
    final l = context.l;
    final amount = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => AlertDialog(
        title: Text(l.contribute),
        content: TextField(controller: amount, decoration: InputDecoration(labelText: l.amount, prefixText: 'UGX '), keyboardType: TextInputType.number),
        actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.confirm))],
      ),
    );
    final m = Money.tryParse(amount.text);
    if (ok != true || m == null || !mounted) return;
    _key ??= const Uuid().v4();
    final d = await guarded(context, () => ref.read(parentApiProvider).contribute(widget.id, {'amount': m.toApi(), 'channel': 'momo', 'idempotency_key': _key}));
    if (d != null && mounted) {
      _key = null;
      await Navigator.of(context).push(MaterialPageRoute(builder: (_) => DepositStatusScreen(deposit: d)));
    }
  }
}

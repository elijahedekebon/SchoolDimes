import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/api/api_client.dart';
import '../../core/api/parent_api.dart';
import '../../core/money/money.dart';
import '../../core/ui/widgets.dart';
import 'deposit_flow.dart';

/// Top up a child's wallet. Also opened pre-filled from a low-balance
/// notification (wallet + suggested amount from its payload).
class TopUpScreen extends ConsumerStatefulWidget {
  const TopUpScreen({super.key, this.initialWalletId, this.suggestedAmount});
  final int? initialWalletId;
  final String? suggestedAmount;
  @override
  ConsumerState<TopUpScreen> createState() => _TopUpScreenState();
}

class _TopUpScreenState extends ConsumerState<TopUpScreen> {
  final _draft = DepositDraft();
  late final _amount = TextEditingController(text: widget.suggestedAmount == null ? '' : Money.parse(widget.suggestedAmount!).toApi().replaceAll('.00', ''));
  final _phone = TextEditingController();
  int? _wallet;
  String _channel = 'momo';
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _wallet = widget.initialWalletId;
    _phone.text = (ref.read(authProvider).value?.me?['phone_number'] as String?) ?? '';
  }

  Future<void> _pay() async {
    final m = Money.tryParse(_amount.text);
    if (m == null || !m.isPositive || _wallet == null) {
      setState(() => _error = context.l.amountInvalid);
      return;
    }
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      // same key on every retry of this top-up (see DepositDraft)
      final d = await _draft.submit(ref.read(parentApiProvider), walletId: _wallet!, amount: m.toApi(), channel: _channel, payerPhone: _phone.text.trim());
      if (!mounted) return;
      await Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => DepositStatusScreen(deposit: d)));
    } on ApiException catch (e) {
      if (mounted) setState(() => _error = errorText(context, e));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final students = ref.watch(dashboardProvider).value?.students ?? const <Json>[];
    _wallet ??= students.isEmpty ? null : students.first['main_wallet']['id'] as int;
    final m = Money.tryParse(_amount.text);
    return Scaffold(
      appBar: AppBar(title: Text(l.topUpTitle)),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        DropdownButtonFormField<int>(
          key: const Key('topup-child'),
          initialValue: _wallet,
          decoration: InputDecoration(labelText: l.child),
          items: [for (final s in students) DropdownMenuItem(value: s['main_wallet']['id'] as int, child: Text(s['name'] as String))],
          onChanged: (v) => setState(() => _wallet = v),
        ),
        TextField(
          key: const Key('topup-amount'),
          controller: _amount,
          decoration: InputDecoration(labelText: l.amount, prefixText: 'UGX '),
          keyboardType: const TextInputType.numberWithOptions(decimal: true),
          onChanged: (_) => setState(() {}),
        ),
        Wrap(spacing: 8, children: [
          for (final a in ['2000', '5000', '10000', '20000'])
            ActionChip(label: Text(Money.parse(a).format()), onPressed: () => setState(() => _amount.text = a)),
        ]),
        const SizedBox(height: 12),
        Text(l.channel, style: Theme.of(context).textTheme.labelLarge),
        SegmentedButton<String>(
          segments: [
            ButtonSegment(value: 'momo', label: Text(l.channel_momo)),
            ButtonSegment(value: 'ussd', label: Text(l.channel_ussd)),
            ButtonSegment(value: 'bank', label: Text(l.channel_bank)),
          ],
          selected: {_channel},
          onSelectionChanged: (s) => setState(() => _channel = s.first),
        ),
        if (_channel != 'bank') TextField(controller: _phone, decoration: InputDecoration(labelText: l.payerPhone), keyboardType: TextInputType.phone),
        if (_error != null) Padding(padding: const EdgeInsets.only(top: 12), child: Text(_error!, key: const Key('topup-error'), style: TextStyle(color: Theme.of(context).colorScheme.error))),
        const SizedBox(height: 24),
        FilledButton(
          key: const Key('topup-pay'),
          onPressed: _busy ? null : _pay,
          child: _busy ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2)) : Text(l.payNow(m == null ? '' : m.format())),
        ),
      ]),
    );
  }
}

/// Shows the channel instructions and polls until confirmed/failed/expired.
class DepositStatusScreen extends ConsumerStatefulWidget {
  const DepositStatusScreen({super.key, required this.deposit});
  final Json deposit;
  @override
  ConsumerState<DepositStatusScreen> createState() => _DepositStatusScreenState();
}

class _DepositStatusScreenState extends ConsumerState<DepositStatusScreen> {
  late Json _d = widget.deposit;
  StreamSubscription<Json>? _sub;
  bool _gaveUp = false;

  @override
  void initState() {
    super.initState();
    if (_d['status'] == 'pending') {
      _sub = pollDeposit(ref.read(parentApiProvider), _d['id'] as int).listen(
        (d) {
          setState(() => _d = d);
          if (d['status'] == 'confirmed') ref.read(dashboardProvider.notifier).refresh();
        },
        onDone: () => mounted && _d['status'] == 'pending' ? setState(() => _gaveUp = true) : null,
        onError: (_) => mounted ? setState(() => _gaveUp = true) : null,
      );
    }
  }

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final status = _d['status'] as String;
    final ins = (_d['instructions'] as Map?)?.cast<String, dynamic>();
    final (icon, color, text) = switch (status) {
      'confirmed' => (Icons.check_circle, Colors.green, l.depositStatus_confirmed),
      'failed' => (Icons.error, Colors.red, l.depositStatus_failed),
      'expired' => (Icons.timer_off, Colors.red, l.depositStatus_expired),
      _ => (Icons.hourglass_top, Colors.orange, l.depositStatus_pending),
    };
    return Scaffold(
      appBar: AppBar(title: Text(l.topUpTitle)),
      body: ListView(padding: const EdgeInsets.all(24), children: [
        Icon(icon, size: 80, color: color),
        Text(money(_d['amount']), textAlign: TextAlign.center, style: Theme.of(context).textTheme.headlineMedium),
        Text(text, key: const Key('deposit-status'), textAlign: TextAlign.center, style: Theme.of(context).textTheme.titleMedium),
        if ((_d['failure_reason'] as String?)?.isNotEmpty == true) Text(_d['failure_reason'] as String, textAlign: TextAlign.center),
        if (status == 'pending' && ins != null)
          Card(
            margin: const EdgeInsets.symmetric(vertical: 16),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
                Text(l.howToPay, style: Theme.of(context).textTheme.titleSmall),
                Text(ins['message'] as String? ?? ''),
                if (ins['ussd_code'] != null) SelectableText(ins['ussd_code'] as String, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                if (ins['account_number'] != null) SelectableText('${ins['bank_name']} · ${ins['account_name']} · ${ins['account_number']} · ${ins['narration']}'),
              ]),
            ),
          ),
        if (status == 'pending' && !_gaveUp) Row(mainAxisAlignment: MainAxisAlignment.center, children: [const SizedBox(width: 16, height: 16, child: CircularProgressIndicator(strokeWidth: 2)), const SizedBox(width: 8), Text(l.waitingConfirmation)]),
        if (status == 'pending' && _gaveUp) Text(l.stillWaiting, textAlign: TextAlign.center),
        const SizedBox(height: 8),
        Text(l.reference(_d['reference'] as String? ?? ''), textAlign: TextAlign.center, style: Theme.of(context).textTheme.bodySmall),
        const SizedBox(height: 24),
        FilledButton(onPressed: () => Navigator.pop(context), child: Text(l.done)),
      ]),
    );
  }
}

class DepositHistoryScreen extends ConsumerWidget {
  const DepositHistoryScreen({super.key, this.fromContributors = false});
  final bool fromContributors;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    return Scaffold(
      appBar: AppBar(title: Text(fromContributors ? l.contributionsReceived : l.depositHistory)),
      body: Loader<Json>(
        load: () => ref.read(parentApiProvider).deposits(filters: {if (fromContributors) 'from_contributor': 'true'}),
        builder: (c, page, _) {
          final rows = (page['results'] as List).cast<Map>();
          if (rows.isEmpty) return ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingYet))]);
          return ListView(children: [
            for (final d in rows)
              ListTile(
                title: Text('${money(d['amount'])} · ${d['contributor_name'] ?? l.topUp}'),
                subtitle: Text('${shortDate(d['created_at'] as String?)} · ${d['reference']}'),
                trailing: Text(d['status'] as String),
                onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => DepositStatusScreen(deposit: d.cast<String, dynamic>()))),
              ),
          ]);
        },
      ),
    );
  }
}

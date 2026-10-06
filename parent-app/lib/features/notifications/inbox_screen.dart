import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/config/env.dart';
import '../../core/ui/widgets.dart';
import '../child/child_screen.dart';
import '../more/more_screen.dart';
import '../payments/payments_screen.dart';
import '../topup/topup_screen.dart';
import 'deep_links.dart';

/// Opens the screen a notification points to.
Future<void> openDeepLink(BuildContext context, WidgetRef ref, DeepLink link) async {
  final nav = Navigator.of(context);
  Json? student() => link.studentId == null ? null : ref.read(dashboardProvider).value?.students.where((s) => s['id'] == link.studentId).firstOrNull;
  switch (link.destination) {
    case Destination.topUp:
      await nav.push(MaterialPageRoute(builder: (_) => TopUpScreen(initialWalletId: link.walletId, suggestedAmount: link.suggestedAmount)));
    case Destination.depositStatus:
      if (link.id == null) return;
      final d = await guarded(context, () => ref.read(parentApiProvider).deposit(link.id!));
      if (d != null) await nav.push(MaterialPageRoute(builder: (_) => DepositStatusScreen(deposit: d)));
    case Destination.childHistory || Destination.savings || Destination.card || Destination.p2p:
      final s = student();
      if (s == null) return;
      final tab = switch (link.destination) { Destination.savings => ChildTab.savings, Destination.card || Destination.p2p => ChildTab.card, _ => ChildTab.history };
      await nav.push(MaterialPageRoute(builder: (_) => ChildScreen(student: s, initialTab: tab)));
    case Destination.recurring:
      await nav.push(MaterialPageRoute(builder: (_) => const RecurringScreen()));
    case Destination.dispute:
      await nav.push(MaterialPageRoute(builder: (_) => const DisputesScreen()));
    case Destination.pooledFund:
      if (link.id != null) await nav.push(MaterialPageRoute(builder: (_) => FundDetailScreen(id: link.id!)));
    case Destination.privacy:
      await nav.push(MaterialPageRoute(builder: (_) => const PrivacyScreen()));
    case Destination.inbox:
      break;
  }
}

class InboxScreen extends ConsumerStatefulWidget {
  const InboxScreen({super.key});
  @override
  ConsumerState<InboxScreen> createState() => _InboxScreenState();
}

class _InboxScreenState extends ConsumerState<InboxScreen> {
  int _gen = 0;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    return Column(children: [
      Row(children: [
        TextButton.icon(
          onPressed: () async {
            if (await guarded(context, api.markAllRead) != null) {
              setState(() => _gen++);
              ref.read(dashboardProvider.notifier).refresh();
            }
          },
          icon: const Icon(Icons.done_all),
          label: Text(l.markAllRead),
        ),
        const Spacer(),
        IconButton(icon: const Icon(Icons.settings), tooltip: l.notificationSettings, onPressed: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const NotificationSettingsScreen()))),
      ]),
      Expanded(
        child: Loader<Json>(
          key: ValueKey(_gen),
          load: () => api.notifications(),
          builder: (c, page, _) {
            final rows = (page['results'] as List).cast<Map>();
            if (rows.isEmpty) return ListView(children: [Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingYet))]);
            return ListView(children: [
              for (final n in rows)
                ListTile(
                  key: Key('notification-${n['id']}'),
                  leading: Icon(n['read_at'] == null ? Icons.circle : Icons.circle_outlined, size: 12, color: Theme.of(context).colorScheme.primary),
                  title: Text(n['title'] as String, style: TextStyle(fontWeight: n['read_at'] == null ? FontWeight.bold : null)),
                  subtitle: Text('${n['body']}\n${shortDate(n['created_at'] as String?)}'),
                  isThreeLine: true,
                  onTap: () async {
                    if (n['read_at'] == null) api.markRead(n['id'] as int).ignore();
                    await openDeepLink(context, ref, deepLinkFor(n['event_type'] as String, (n['payload'] as Map).cast<String, dynamic>()));
                    if (mounted) setState(() => _gen++);
                  },
                ),
            ]);
          },
        ),
      ),
    ]);
  }
}

class NotificationSettingsScreen extends ConsumerWidget {
  const NotificationSettingsScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    return Scaffold(
      appBar: AppBar(title: Text(l.notificationSettings)),
      body: Loader<Json>(
        load: api.preferences,
        builder: (c, p, reload) => ListView(children: [
          for (final (key, label) in [('in_app_enabled', l.channelInApp), ('sms_enabled', l.channelSms), ('push_enabled', l.channelPush)])
            SwitchListTile(
              title: Text(label),
              value: p[key] == true,
              onChanged: (v) async {
                if (await guarded(context, () => api.updatePreferences({key: v}), success: l.saved) != null) reload();
              },
            ),
          if (!Env.pushEnabled) Padding(padding: const EdgeInsets.all(16), child: Text(l.pushNotConfigured, style: Theme.of(context).textTheme.bodySmall)),
        ]),
      ),
    );
  }
}

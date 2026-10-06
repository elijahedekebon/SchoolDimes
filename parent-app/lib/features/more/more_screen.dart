import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:share_plus/share_plus.dart';

import '../../app/app_lock.dart';
import '../../app/providers.dart';
import '../../core/api/parent_api.dart';
import '../../core/ui/widgets.dart';
import '../kyc/kyc_screen.dart';

class MoreScreen extends ConsumerWidget {
  const MoreScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final me = ref.watch(authProvider).value?.me ?? const {};
    final status = ref.watch(dashboardProvider).value?.verificationStatus;
    final lock = ref.watch(appLockProvider).value ?? false;
    void go(Widget w) => Navigator.of(context).push(MaterialPageRoute(builder: (_) => w));
    return ListView(children: [
      ListTile(leading: const Icon(Icons.person), title: Text(me['full_name'] as String? ?? ''), subtitle: Text(me['email'] as String? ?? ''), onTap: () => go(const ProfileScreen())),
      ListTile(
        leading: Icon(status == 'verified' ? Icons.verified : Icons.badge_outlined),
        title: Text(l.kycTitle),
        subtitle: Text(switch (status) { 'pending' => l.kycStatus_pending, 'verified' => l.kycStatus_verified, 'rejected' => l.kycStatus_rejected, _ => l.kycStatus_none }),
        onTap: () => go(const KycScreen()),
      ),
      SwitchListTile(secondary: const Icon(Icons.fingerprint), title: Text(l.appLock), subtitle: Text(l.appLockHelp), value: lock, onChanged: (v) => ref.read(appLockProvider.notifier).set(v)),
      ListTile(leading: const Icon(Icons.report_problem_outlined), title: Text(l.disputesTitle), onTap: () => go(const DisputesScreen())),
      ListTile(leading: const Icon(Icons.privacy_tip_outlined), title: Text(l.privacyTitle), onTap: () => go(const PrivacyScreen())),
      ListTile(
        key: const Key('sign-out'),
        leading: const Icon(Icons.logout),
        title: Text(l.signOut),
        onTap: () => ref.read(authProvider.notifier).logout(),
      ),
    ]);
  }
}

class ProfileScreen extends ConsumerStatefulWidget {
  const ProfileScreen({super.key});
  @override
  ConsumerState<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends ConsumerState<ProfileScreen> {
  late final me = ref.read(authProvider).value?.me ?? const {};
  late final _name = TextEditingController(text: me['full_name'] as String? ?? '');
  late final _phone = TextEditingController(text: me['phone_number'] as String? ?? '');
  late String _lang = me['preferred_language'] as String? ?? 'en';

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    return Scaffold(
      appBar: AppBar(title: Text(l.profile)),
      body: ListView(padding: const EdgeInsets.all(16), children: [
        TextField(controller: _name, decoration: InputDecoration(labelText: l.fullName)),
        TextField(controller: _phone, decoration: InputDecoration(labelText: l.phone), keyboardType: TextInputType.phone),
        DropdownButtonFormField<String>(
          key: const Key('language'),
          initialValue: _lang,
          decoration: InputDecoration(labelText: l.language),
          items: const [
            DropdownMenuItem(value: 'en', child: Text('English')),
            DropdownMenuItem(value: 'lg', child: Text('Luganda')),
            DropdownMenuItem(value: 'sw', child: Text('Kiswahili')),
          ],
          onChanged: (v) => setState(() => _lang = v ?? 'en'),
        ),
        const SizedBox(height: 16),
        FilledButton(
          onPressed: () => guarded(context, () => ref.read(authProvider.notifier).updateProfile({'full_name': _name.text.trim(), 'phone_number': _phone.text.trim(), 'preferred_language': _lang}), success: l.saved),
          child: Text(l.save),
        ),
      ]),
    );
  }
}

class DisputesScreen extends ConsumerWidget {
  const DisputesScreen({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    return Scaffold(
      appBar: AppBar(title: Text(l.disputesTitle)),
      body: Loader<List<Json>>(
        load: ref.read(parentApiProvider).disputes,
        builder: (c, rows, _) => ListView(children: [
          if (rows.isEmpty) Padding(padding: const EdgeInsets.all(24), child: Text(l.nothingYet)),
          for (final d in rows)
            ListTile(
              title: Text('${d['student_name']} · ${money(d['original_amount'])}'),
              subtitle: Text('${shortDate(d['created_at'] as String?)}${(d['resolution_notes'] as String?)?.isNotEmpty == true ? '\n${d['resolution_notes']}' : ''}'),
              trailing: Text(switch (d['status']) {
                'under_review' => l.dispute_under_review,
                'resolved_refunded' => l.dispute_resolved_refunded(money(d['refund_amount'])),
                'resolved_denied' => l.dispute_resolved_denied,
                _ => l.dispute_open,
              }),
            ),
        ]),
      ),
    );
  }
}

class PrivacyScreen extends ConsumerStatefulWidget {
  const PrivacyScreen({super.key});
  @override
  ConsumerState<PrivacyScreen> createState() => _PrivacyScreenState();
}

class _PrivacyScreenState extends ConsumerState<PrivacyScreen> {
  int _gen = 0;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final api = ref.read(parentApiProvider);
    String status(String s) => switch (s) { 'in_progress' => l.request_in_progress, 'completed' => l.request_completed, 'rejected' => l.request_rejected, _ => l.request_pending };
    String type(String s) => switch (s) { 'correction' => l.request_correction, 'deletion' => l.request_deletion, _ => l.request_export };
    return Scaffold(
      appBar: AppBar(title: Text(l.privacyTitle)),
      body: ListView(key: ValueKey(_gen), padding: const EdgeInsets.all(16), children: [
        ListTile(leading: const Icon(Icons.visibility), title: Text(l.myData), onTap: () => Navigator.of(context).push(MaterialPageRoute(builder: (_) => const _MyDataScreen()))),
        ListTile(
          leading: const Icon(Icons.download),
          title: Text(l.downloadCsv),
          onTap: () async {
            final csv = await guarded(context, api.myDataCsv);
            if (csv != null) await SharePlus.instance.share(ShareParams(files: [XFile.fromData(utf8.encode(csv), mimeType: 'text/csv', name: 'schooldimes-my-data.csv')], fileNameOverrides: ['schooldimes-my-data.csv']));
          },
        ),
        const Divider(),
        Row(children: [Text(l.dataRequests, style: Theme.of(context).textTheme.titleMedium), const Spacer(), TextButton.icon(onPressed: _newRequest, icon: const Icon(Icons.add), label: Text(l.newDataRequest))]),
        Loader<List<Json>>(
          load: api.dataRequests,
          builder: (c, rows, _) => Column(children: [
            if (rows.isEmpty) Text(l.nothingYet),
            for (final r in rows)
              ListTile(
                title: Text(type(r['request_type'] as String)),
                subtitle: Text([shortDate(r['created_at'] as String?), if ((r['notes'] as String?)?.isNotEmpty == true) r['notes'] as String, if (r['retention_notice'] != null) r['retention_notice'] as String].join('\n')),
                trailing: Text(status(r['status'] as String)),
              ),
          ]),
        ),
      ]),
    );
  }

  Future<void> _newRequest() async {
    final l = context.l;
    final students = ref.read(dashboardProvider).value?.students ?? const <Json>[];
    String type = 'export';
    int? subject; // null = me
    final details = TextEditingController();
    final ok = await showDialog<bool>(
      context: context,
      builder: (c) => StatefulBuilder(
        builder: (c, set) => AlertDialog(
          title: Text(l.newDataRequest),
          content: SingleChildScrollView(
            child: Column(mainAxisSize: MainAxisSize.min, children: [
              DropdownButtonFormField<String>(initialValue: type, items: [for (final t in ['export', 'correction', 'deletion']) DropdownMenuItem(value: t, child: Text(switch (t) { 'correction' => l.request_correction, 'deletion' => l.request_deletion, _ => l.request_export }))], onChanged: (v) => set(() => type = v ?? 'export')),
              DropdownButtonFormField<int?>(
                initialValue: subject,
                items: [DropdownMenuItem(value: null, child: Text(l.aboutMe)), for (final s in students) DropdownMenuItem(value: s['id'] as int, child: Text(l.aboutChild(s['first_name'] as String)))],
                onChanged: (v) => set(() => subject = v),
              ),
              TextField(controller: details, decoration: InputDecoration(labelText: l.requestDetails), maxLines: 3),
              if (type == 'deletion') Padding(padding: const EdgeInsets.only(top: 8), child: Text(l.retentionNotice, style: Theme.of(c).textTheme.bodySmall)),
            ]),
          ),
          actions: [TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)), FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.confirm))],
        ),
      ),
    );
    if (ok != true || !mounted) return;
    final r = await guarded(context, () => ref.read(parentApiProvider).createDataRequest({'request_type': type, 'subject': subject == null ? 'self' : 'student', 'student': subject, 'details': details.text.trim()}));
    if (r != null) setState(() => _gen++);
  }
}

class _MyDataScreen extends ConsumerWidget {
  const _MyDataScreen();
  @override
  Widget build(BuildContext context, WidgetRef ref) => Scaffold(
        appBar: AppBar(title: Text(context.l.myData)),
        body: Loader<Json>(
          load: ref.read(parentApiProvider).myData,
          builder: (c, d, _) {
            final profile = (d['profile'] as Map?) ?? {};
            final students = ((d['students'] as List?) ?? const []).cast<Map>();
            return ListView(padding: const EdgeInsets.all(16), children: [
              for (final e in profile.entries) ListTile(dense: true, title: Text('${e.key}'), subtitle: Text('${e.value}')),
              for (final s in students) ...[
                const Divider(),
                Text('${s['name']} · ${s['class_name']}', style: Theme.of(context).textTheme.titleMedium),
                for (final w in (s['wallets'] as List).cast<Map>()) ListTile(dense: true, title: Text('${w['wallet_type']}'), trailing: Text(money(w['balance'])), subtitle: Text('${(w['ledger'] as List).length} entries')),
              ],
            ]);
          },
        ),
      );
}

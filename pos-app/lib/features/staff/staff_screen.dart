import 'dart:async';

import 'package:drift/drift.dart' hide Column;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:local_auth/local_auth.dart';

import '../../app/services.dart';
import '../../app/session.dart';
import '../../core/config/env.dart';
import '../../core/db/database.dart';
import '../../core/money/money.dart';
import '../../core/security/secure_store.dart';
import '../../core/time/kampala.dart';
import '../../core/ui/widgets.dart';
import '../provisioning/setup_screen.dart';

/// Staff-only area behind the local staff PIN (optionally the staff
/// member's own fingerprint via local_auth — never used for students).
class StaffScreen extends ConsumerStatefulWidget {
  const StaffScreen({super.key});
  @override
  ConsumerState<StaffScreen> createState() => _StaffScreenState();
}

class _StaffScreenState extends ConsumerState<StaffScreen> {
  bool _unlocked = false;
  String _pin = '';
  String? _error;

  Future<void> _check() async {
    final hash = ref.read(sessionProvider).requireValue.config!.adminPinHash;
    if (checkAdminPin(_pin, hash)) {
      setState(() => _unlocked = true);
    } else {
      setState(() {
        _error = context.l.adminPinWrong;
        _pin = '';
      });
    }
  }

  Future<void> _biometric() async {
    try {
      final ok = await LocalAuthentication().authenticate(localizedReason: context.l.staffTitle);
      if (ok && mounted) setState(() => _unlocked = true);
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    if (!_unlocked) {
      return Column(
        children: [
          const StatusBar(),
          Expanded(
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 360),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(l.enterAdminPin, style: Theme.of(context).textTheme.titleLarge),
                    Text(List.filled(_pin.length, '●').join(' '), style: const TextStyle(fontSize: 28)),
                    if (_error != null) Text(_error!, style: TextStyle(color: Theme.of(context).colorScheme.error)),
                    NumPad(
                      onKey: (k) => _pin.length < 8 ? setState(() => _pin += k) : null,
                      onBackspace: () =>
                          _pin.isNotEmpty ? setState(() => _pin = _pin.substring(0, _pin.length - 1)) : null,
                      onDone: _pin.length >= 4 ? _check : null,
                      doneLabel: l.confirm,
                    ),
                    TextButton.icon(
                      onPressed: _biometric,
                      icon: const Icon(Icons.fingerprint),
                      label: Text(l.useBiometrics),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ],
      );
    }
    return DefaultTabController(
      length: 4,
      child: Column(
        children: [
          const StatusBar(),
          TabBar(
            isScrollable: true,
            tabs: [
              Tab(text: l.todaySummary),
              Tab(text: l.needsReview),
              Tab(text: l.rejectedList),
              Tab(text: l.settings),
            ],
          ),
          const Expanded(
            child: TabBarView(
              children: [_Today(), _ReviewList(rejected: false), _ReviewList(rejected: true), _Settings()],
            ),
          ),
        ],
      ),
    );
  }
}

final _todayProvider = StreamProvider<(List<SaleQueueData>, List<AttendanceQueueData>)>((ref) async* {
  final db = ref.watch(sessionProvider).requireValue.db;
  while (true) {
    try {
      final day = Kampala.day(DateTime.now());
      final sales = await (db.select(db.saleQueue)..where((s) => s.kampalaDay.equals(day))).get();
      final taps = await (db.select(db.attendanceQueue)..where((s) => s.kampalaDay.equals(day))).get();
      yield (sales, taps);
    } on StateError {
      return; // database closed
    }
    await Future<void>.delayed(const Duration(seconds: 3));
  }
});

class _Today extends ConsumerWidget {
  const _Today();
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final data = ref.watch(_todayProvider).value;
    if (data == null) return const Center(child: CircularProgressIndicator());
    final (sales, taps) = data;
    final done = sales.where((s) => s.status != 'refused' && s.status != 'rejected').toList();
    final pending = done.where((s) => s.status == 'pending').length;
    final total = Money.sum(done.map((s) => Money(s.amountCents)));
    final tapsPending = taps.where((t) => t.status == 'pending').length;
    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        Card(
          child: ListTile(
            leading: const Icon(Icons.point_of_sale),
            title: Text(l.salesCount(done.length), key: const Key('today-sales')),
            subtitle: Text('${l.salesTotal(total.format())}\n${l.syncedVsPending(done.length - pending, pending)}'),
            isThreeLine: true,
          ),
        ),
        Card(
          child: ListTile(
            leading: const Icon(Icons.how_to_reg),
            title: Text(l.tapsCount(taps.length)),
            subtitle: Text(l.syncedVsPending(taps.length - tapsPending, tapsPending)),
          ),
        ),
      ],
    );
  }
}

class _ReviewList extends ConsumerWidget {
  const _ReviewList({required this.rejected});
  final bool rejected;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final l = context.l;
    final db = ref.watch(sessionProvider).requireValue.db;
    final q = db.select(db.saleQueue)
      ..where((s) => rejected ? s.status.equals('rejected') : (s.status.equals('shortfall') | s.flags.isNotValue('')))
      ..orderBy([(s) => OrderingTerm.desc(s.createdAt)]);
    final tapsQ = db.select(db.attendanceQueue)..where((t) => t.status.equals('rejected'));
    return StreamBuilder<List<SaleQueueData>>(
      stream: q.watch(),
      builder: (_, snap) => StreamBuilder<List<AttendanceQueueData>>(
        stream: rejected ? tapsQ.watch() : Stream.value(const []),
        builder: (_, tsnap) {
          final rows = snap.data ?? const [];
          final taps = tsnap.data ?? const [];
          return ListView(
            padding: const EdgeInsets.all(8),
            children: [
              Padding(padding: const EdgeInsets.all(8), child: Text(rejected ? l.rejectedHelp : l.needsReviewHelp)),
              if (rows.isEmpty && taps.isEmpty) Padding(padding: const EdgeInsets.all(16), child: Text(l.nothingHere)),
              for (final s in rows)
                ListTile(
                  leading: Icon(
                    rejected ? Icons.block : Icons.report_problem,
                    color: rejected ? Colors.red : Colors.orange,
                  ),
                  title: Text('${s.studentName} — ${Money(s.amountCents).format()}'),
                  subtitle: Text(
                    [
                      s.deviceLocalTimestamp.replaceFirst('T', ' ').substring(0, 16),
                      if (s.shortfallCents != null && s.shortfallCents! > 0)
                        'shortfall ${Money(s.shortfallCents!).format()}',
                      if (s.flags.isNotEmpty) s.flags.split(',').map((f) => reasonText(l, f)).join('; '),
                      if (s.reason != null) s.reason!,
                    ].join(' · '),
                  ),
                ),
              for (final t in taps)
                ListTile(
                  leading: const Icon(Icons.block, color: Colors.red),
                  title: Text('${t.studentName} (${t.direction})'),
                  subtitle: Text('${t.deviceLocalTimestamp} · ${t.reason ?? ''}'),
                ),
            ],
          );
        },
      ),
    );
  }
}

class _Settings extends ConsumerStatefulWidget {
  const _Settings();
  @override
  ConsumerState<_Settings> createState() => _SettingsState();
}

class _SettingsState extends ConsumerState<_Settings> {
  bool _busy = false;

  Future<void> _wrap(Future<void> Function() f, String done) async {
    setState(() => _busy = true);
    try {
      await f();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(done)));
    } catch (e) {
      if (mounted) showError(context, context.l.error(e.toString()));
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final session = ref.watch(sessionProvider).requireValue;
    final cfg = session.config!;
    final lang = ref.watch(localeProvider).value ?? 'en';
    final role = switch (cfg.role) {
      'merchant' => l.roleMerchant,
      'attendance' => l.roleAttendance,
      _ => l.roleCanteen,
    };
    return ListView(
      padding: const EdgeInsets.all(8),
      children: [
        ListTile(
          leading: const Icon(Icons.language),
          title: Text(l.language),
          trailing: DropdownButton<String>(
            value: lang,
            items: const [
              DropdownMenuItem(value: 'en', child: Text('English')),
              DropdownMenuItem(value: 'lg', child: Text('Luganda')),
              DropdownMenuItem(value: 'sw', child: Text('Kiswahili')),
            ],
            onChanged: (v) => v == null ? null : ref.read(sessionProvider.notifier).setLanguage(v),
          ),
        ),
        ListTile(
          leading: const Icon(Icons.sync),
          title: Text(l.syncNow),
          enabled: !_busy,
          onTap: () => _wrap(() async {
            final r = await ref.read(syncControllerProvider).run(manual: true);
            if (r.networkFailed) throw Exception(l.syncFailed);
          }, l.syncDone),
        ),
        ListTile(
          leading: const Icon(Icons.download),
          title: Text(l.refreshCache),
          enabled: !_busy,
          onTap: () => _wrap(() async {
            if (cfg.canSell) await ref.read(cacheServiceProvider).refresh(full: true);
            if (cfg.canRecordAttendance) await ref.read(cacheServiceProvider).refreshRoster(full: true);
          }, l.cacheRefreshed),
        ),
        const _LockedCards(),
        const Divider(),
        ListTile(title: Text(l.deviceInfo), subtitle: Text('${cfg.deviceName} · $role')),
        ListTile(title: Text(l.school), subtitle: Text(cfg.schoolName)),
        if (cfg.merchant != null) ListTile(title: Text(l.merchant), subtitle: Text(cfg.merchant!['name'] as String)),
        ListTile(
          title: Text(l.appVersion),
          subtitle: Text('${Env.appVersion} · ${l.flavor}: ${Env.flavor} · ${cfg.baseUrl}'),
        ),
        if (Env.isDev) const _ShowUid(),
        const Divider(),
        ListTile(
          leading: const Icon(Icons.qr_code),
          title: Text(l.reprovision),
          onTap: () async {
            final ok = await showDialog<bool>(
              context: context,
              builder: (c) => AlertDialog(
                content: Text(l.reprovisionConfirm),
                actions: [
                  TextButton(onPressed: () => Navigator.pop(c, false), child: Text(l.cancel)),
                  FilledButton(onPressed: () => Navigator.pop(c, true), child: Text(l.confirm)),
                ],
              ),
            );
            if (ok == true && context.mounted) {
              Navigator.of(context).push(MaterialPageRoute(builder: (_) => const SetupScreen(reprovision: true)));
            }
          },
        ),
      ],
    );
  }
}

class _LockedCards extends ConsumerWidget {
  const _LockedCards();
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final db = ref.watch(sessionProvider).requireValue.db;
    return StreamBuilder<List<PinFailure>>(
      stream: (db.select(db.pinFailures)..where((p) => p.locked.equals(true))).watch(),
      builder: (_, snap) {
        final rows = snap.data ?? const [];
        if (rows.isEmpty) return const SizedBox.shrink();
        return ExpansionTile(
          leading: const Icon(Icons.lock),
          title: Text('${context.l.lockedCards} (${rows.length})'),
          children: [
            for (final r in rows)
              ListTile(
                title: Text(r.cardUid),
                trailing: TextButton(
                  onPressed: () => ref.read(saleServiceProvider).pins.unlock(r.cardUid),
                  child: Text(context.l.unlockCard),
                ),
              ),
          ],
        );
      },
    );
  }
}

/// dev flavor only: read a blank card's UID to issue it in the dashboard.
class _ShowUid extends ConsumerStatefulWidget {
  const _ShowUid();
  @override
  ConsumerState<_ShowUid> createState() => _ShowUidState();
}

class _ShowUidState extends ConsumerState<_ShowUid> {
  String? _uid;
  StreamSubscription<String>? _sub;

  @override
  void dispose() {
    _sub?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    return ListTile(
      leading: const Icon(Icons.nfc),
      title: Text(l.showUid),
      subtitle: Text(
        _uid ?? l.showUidHint,
        key: const Key('shown-uid'),
        style: _uid == null ? null : const TextStyle(fontFamily: 'monospace', fontSize: 18),
      ),
      trailing: _uid == null
          ? null
          : IconButton(
              icon: const Icon(Icons.copy),
              onPressed: () {
                Clipboard.setData(ClipboardData(text: _uid!));
                ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(l.uidCopied)));
              },
            ),
      onTap: () async {
        final reader = ref.read(nfcReaderProvider);
        _sub ??= reader.uids.listen((u) => mounted ? setState(() => _uid = u) : null);
        await reader.start();
      },
    );
  }
}

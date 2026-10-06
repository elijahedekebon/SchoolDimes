import 'dart:async';

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/services.dart';
import '../../core/config/env.dart';
import '../../core/nfc/nfc_reader.dart';
import '../../core/nfc/uid.dart';
import '../../core/ui/widgets.dart';
import 'attendance_service.dart';

/// Full-screen gate mode. A tap skips PIN and amount, is written to the local
/// queue, and the screen is ready for the next student in about a second.
class AttendanceScreen extends ConsumerStatefulWidget {
  const AttendanceScreen({super.key});
  @override
  ConsumerState<AttendanceScreen> createState() => _AttendanceScreenState();
}

class _AttendanceScreenState extends ConsumerState<AttendanceScreen> {
  String _direction = 'in';
  TapResult? _last;
  Timer? _clear;
  StreamSubscription<String>? _sub;
  NfcState? _nfc;
  final _sim = TextEditingController();

  @override
  void initState() {
    super.initState();
    final reader = ref.read(nfcReaderProvider);
    _sub = reader.uids.listen(_onTap);
    reader.start().then((s) => mounted ? setState(() => _nfc = s) : null);
  }

  @override
  void dispose() {
    _sub?.cancel();
    _clear?.cancel();
    _sim.dispose();
    super.dispose();
  }

  Future<void> _onTap(String uid) async {
    final r = await ref.read(attendanceServiceProvider).tap(uid, _direction);
    if (!mounted) return;
    if (r.status == TapStatus.recorded) ref.read(syncControllerProvider).nudge();
    _clear?.cancel();
    setState(() => _last = r);
    _clear = Timer(const Duration(milliseconds: 1500), () => mounted ? setState(() => _last = null) : null);
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final theme = Theme.of(context);
    final r = _last;
    final (Color bg, IconData icon, String text) = switch (r?.status) {
      null => (theme.colorScheme.surface, Icons.contactless, l.tapToRecord),
      TapStatus.recorded => (Colors.green.shade100, Icons.check_circle, _direction == 'in' ? l.welcome(r!.card!.displayName) : l.goodbye(r!.card!.displayName)),
      TapStatus.duplicateIgnored => (Colors.blue.shade50, Icons.check, l.alreadyRecorded(r!.card!.displayName)),
      TapStatus.unknownCard => (Colors.red.shade100, Icons.help_outline, l.tapUnknown),
      TapStatus.lostCard => (Colors.red.shade100, Icons.report, l.tapLost),
    };
    return Column(children: [
      const StatusBar(),
      Padding(
        padding: const EdgeInsets.all(12),
        child: SegmentedButton<String>(
          segments: [
            ButtonSegment(value: 'in', label: Text(l.directionIn), icon: const Icon(Icons.login)),
            ButtonSegment(value: 'out', label: Text(l.directionOut), icon: const Icon(Icons.logout)),
          ],
          selected: {_direction},
          onSelectionChanged: (s) => setState(() => _direction = s.first),
        ),
      ),
      Expanded(
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 150),
          color: bg,
          width: double.infinity,
          child: Column(mainAxisAlignment: MainAxisAlignment.center, children: [
            if (r?.card?.photoUrl != null)
              CircleAvatar(radius: 72, backgroundImage: NetworkImage(r!.card!.photoUrl!), onBackgroundImageError: (_, _) {})
            else
              Icon(icon, size: 140, color: theme.colorScheme.primary),
            const SizedBox(height: 24),
            Padding(
              padding: const EdgeInsets.symmetric(horizontal: 24),
              child: Text(text, key: const Key('tap-result'), textAlign: TextAlign.center, style: theme.textTheme.headlineMedium),
            ),
            if (r?.card != null) Text(r!.card!.className, style: theme.textTheme.titleMedium),
            if (_nfc == NfcState.disabled) Padding(padding: const EdgeInsets.all(16), child: Text(l.nfcDisabled, style: TextStyle(color: theme.colorScheme.error))),
          ]),
        ),
      ),
      if (Env.isDev)
        Padding(
          padding: const EdgeInsets.all(8),
          child: Row(children: [
            Expanded(child: TextField(key: const Key('simulate-uid'), controller: _sim, decoration: InputDecoration(labelText: l.simulateTap, isDense: true))),
            IconButton(
              key: const Key('simulate-tap'),
              onPressed: () {
                final uid = normalizeUid(_sim.text);
                if (uid != null) ref.read(nfcReaderProvider).emit(uid);
              },
              icon: const Icon(Icons.nfc),
            ),
          ]),
        ),
    ]);
  }
}

import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:local_auth/local_auth.dart';

import '../core/ui/widgets.dart';

/// Optional lock with the phone's own biometrics/PIN (local_auth). Unlike
/// the shared POS terminal, this is the parent's own phone, so device
/// biometrics identify the right person.
class AppLockNotifier extends AsyncNotifier<bool> {
  static const _s = FlutterSecureStorage();
  @override
  Future<bool> build() async => await _s.read(key: 'app_lock') == '1';

  Future<void> set(bool enabled) async {
    if (enabled && !await authenticate('SchoolDimes')) return;
    await _s.write(key: 'app_lock', value: enabled ? '1' : '0');
    state = AsyncData(enabled);
  }

  static Future<bool> authenticate(String reason) async {
    try {
      return await LocalAuthentication().authenticate(localizedReason: reason);
    } catch (_) {
      return false;
    }
  }
}

final appLockProvider = AsyncNotifierProvider<AppLockNotifier, bool>(AppLockNotifier.new);

/// Shows [child] once unlocked; locks again when the app goes to the background.
class LockGate extends ConsumerStatefulWidget {
  const LockGate({super.key, required this.child});
  final Widget child;
  @override
  ConsumerState<LockGate> createState() => _LockGateState();
}

class _LockGateState extends ConsumerState<LockGate> with WidgetsBindingObserver {
  bool _unlocked = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addObserver(this);
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState s) {
    if (s == AppLifecycleState.paused) setState(() => _unlocked = false);
  }

  @override
  Widget build(BuildContext context) {
    final enabled = ref.watch(appLockProvider).value ?? false;
    if (!enabled || _unlocked) return widget.child;
    return Scaffold(
      body: Center(
        child: FilledButton.icon(
          icon: const Icon(Icons.fingerprint),
          label: Text(context.l.unlock),
          onPressed: () async {
            if (await AppLockNotifier.authenticate(context.l.appTitle)) setState(() => _unlocked = true);
          },
        ),
      ),
    );
  }
}

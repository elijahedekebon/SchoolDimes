import 'package:flutter/cupertino.dart' show CupertinoLocalizations;
import 'package:flutter/material.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../core/l10n/gen/app_localizations.dart';
import '../core/ui/widgets.dart';
import '../features/auth/auth_screens.dart';
import '../features/dashboard/home_screen.dart';
import '../features/kyc/kyc_screen.dart';
import '../features/more/more_screen.dart';
import '../features/notifications/inbox_screen.dart';
import '../features/payments/payments_screen.dart';
import 'app_lock.dart';
import 'providers.dart';

class ParentApp extends ConsumerWidget {
  const ParentApp({super.key});
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lang = ref.watch(authProvider).value?.language ?? 'en';
    return MaterialApp(
      title: 'SchoolDimes',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: const Color(0xFF0E7C66), useMaterial3: true),
      locale: Locale(lang),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        _FallbackMaterial(),
        _FallbackCupertino(),
        GlobalWidgetsLocalizations.delegate,
      ],
      home: const LockGate(child: _Gate()),
    );
  }
}

class _Gate extends ConsumerStatefulWidget {
  const _Gate();
  @override
  ConsumerState<_Gate> createState() => _GateState();
}

class _GateState extends ConsumerState<_Gate> {
  bool _kycSkipped = false;
  @override
  Widget build(BuildContext context) {
    final auth = ref.watch(authProvider);
    return auth.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, _) => const LoginScreen(),
      data: (a) {
        if (!a.signedIn) return const LoginScreen();
        // guided KYC step after sign-up / until submitted (skippable)
        final status = ref.watch(dashboardProvider).value?.verificationStatus;
        final dashLoaded = ref.watch(dashboardProvider).hasValue;
        if (dashLoaded && status == null && !_kycSkipped) return KycScreen(onDone: () => setState(() => _kycSkipped = true));
        return const HomeShell();
      },
    );
  }
}

class HomeShell extends ConsumerStatefulWidget {
  const HomeShell({super.key});
  @override
  ConsumerState<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends ConsumerState<HomeShell> {
  int _tab = 0;
  @override
  Widget build(BuildContext context) {
    final l = context.l;
    final unread = ref.watch(dashboardProvider).value?.unread ?? 0;
    final pages = [const HomeScreen(), const PaymentsScreen(), const InboxScreen(), const MoreScreen()];
    final titles = [l.homeTitle, l.payments, l.inbox, l.more];
    return Scaffold(
      appBar: AppBar(title: Text(titles[_tab])),
      body: SafeArea(child: pages[_tab]),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _tab,
        onDestinationSelected: (i) {
          setState(() => _tab = i);
          if (i == 0) ref.read(dashboardProvider.notifier).refresh();
        },
        destinations: [
          NavigationDestination(icon: const Icon(Icons.home_outlined), selectedIcon: const Icon(Icons.home), label: l.homeTitle),
          NavigationDestination(icon: const Icon(Icons.payments_outlined), label: l.payments),
          NavigationDestination(icon: Badge(isLabelVisible: unread > 0, label: Text('$unread'), child: const Icon(Icons.notifications_outlined)), label: l.inbox),
          NavigationDestination(icon: const Icon(Icons.menu), label: l.more),
        ],
      ),
    );
  }
}

/// Flutter has no Luganda widget strings: English fallback for those only.
class _FallbackMaterial extends LocalizationsDelegate<MaterialLocalizations> {
  const _FallbackMaterial();
  @override
  bool isSupported(Locale locale) => true;
  @override
  Future<MaterialLocalizations> load(Locale locale) =>
      GlobalMaterialLocalizations.delegate.load(GlobalMaterialLocalizations.delegate.isSupported(locale) ? locale : const Locale('en'));
  @override
  bool shouldReload(covariant LocalizationsDelegate<MaterialLocalizations> old) => false;
}

class _FallbackCupertino extends LocalizationsDelegate<CupertinoLocalizations> {
  const _FallbackCupertino();
  @override
  bool isSupported(Locale locale) => true;
  @override
  Future<CupertinoLocalizations> load(Locale locale) =>
      GlobalCupertinoLocalizations.delegate.load(GlobalCupertinoLocalizations.delegate.isSupported(locale) ? locale : const Locale('en'));
  @override
  bool shouldReload(covariant LocalizationsDelegate<CupertinoLocalizations> old) => false;
}

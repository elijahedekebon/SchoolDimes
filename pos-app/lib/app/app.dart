import 'package:flutter/cupertino.dart' show CupertinoLocalizations;
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:flutter_localizations/flutter_localizations.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:wakelock_plus/wakelock_plus.dart';

import '../core/l10n/gen/app_localizations.dart';
import '../core/ui/widgets.dart';
import '../features/attendance/attendance_screen.dart';
import '../features/p2p/p2p_screen.dart';
import '../features/provisioning/setup_screen.dart';
import '../features/sale/sale_screen.dart';
import '../features/staff/staff_screen.dart';
import 'services.dart';
import 'session.dart';

class PosApp extends ConsumerWidget {
  const PosApp({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final lang = ref.watch(localeProvider).value ?? 'en';
    return MaterialApp(
      title: 'SchoolDimes POS',
      debugShowCheckedModeBanner: false,
      theme: ThemeData(colorSchemeSeed: const Color(0xFF0E7C66), useMaterial3: true, visualDensity: VisualDensity.comfortable),
      locale: Locale(lang),
      supportedLocales: AppLocalizations.supportedLocales,
      localizationsDelegates: const [
        AppLocalizations.delegate,
        FallbackMaterialLocalizationsDelegate(),
        FallbackCupertinoLocalizationsDelegate(),
        GlobalWidgetsLocalizations.delegate,
      ],
      home: const _Gate(),
    );
  }
}

/// Setup until provisioned; the revoked screen once the server refuses the
/// token; otherwise the role's home.
class _Gate extends ConsumerWidget {
  const _Gate();

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final session = ref.watch(sessionProvider);
    return session.when(
      loading: () => const Scaffold(body: Center(child: CircularProgressIndicator())),
      error: (e, _) => Scaffold(body: Center(child: Padding(padding: const EdgeInsets.all(24), child: Text(context.l.error(e.toString()))))),
      data: (s) {
        if (!s.provisioned) return const SetupScreen();
        if (s.revoked) return const RevokedScreen();
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
  void initState() {
    super.initState();
    WakelockPlus.enable(); // counter terminal: the screen never sleeps
    SystemChrome.setPreferredOrientations([DeviceOrientation.portraitUp]);
  }

  @override
  void dispose() {
    WakelockPlus.disable();
    ref.read(nfcReaderProvider).stop();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final l = context.l;
    ref.watch(syncControllerProvider); // starts timers + connectivity triggers
    final cfg = ref.watch(sessionProvider).requireValue.config!;
    final tabs = <(String, IconData, Widget)>[
      if (cfg.canSell) (l.menuSale, Icons.point_of_sale, const SaleScreen()),
      if (cfg.canP2p) (l.menuP2p, Icons.swap_horiz, const P2PScreen()),
      if (cfg.canRecordAttendance) (l.menuAttendance, Icons.how_to_reg, const AttendanceScreen()),
      (l.menuStaff, Icons.admin_panel_settings, const StaffScreen()),
    ];
    final index = _tab.clamp(0, tabs.length - 1);
    return Scaffold(
      appBar: AppBar(title: Text('${cfg.schoolName} · ${cfg.deviceName}', overflow: TextOverflow.ellipsis)),
      body: SafeArea(child: tabs[index].$3),
      bottomNavigationBar: NavigationBar(
        selectedIndex: index,
        onDestinationSelected: (i) => setState(() => _tab = i),
        destinations: [for (final t in tabs) NavigationDestination(icon: Icon(t.$2), label: t.$1)],
      ),
    );
  }
}

/// Flutter's Material/Cupertino localizations have no Luganda; fall back to
/// English for widget strings (our own strings still come from app_lg.arb).
class FallbackMaterialLocalizationsDelegate extends LocalizationsDelegate<MaterialLocalizations> {
  const FallbackMaterialLocalizationsDelegate();
  @override
  bool isSupported(Locale locale) => true;
  @override
  Future<MaterialLocalizations> load(Locale locale) => GlobalMaterialLocalizations.delegate.isSupported(locale)
      ? GlobalMaterialLocalizations.delegate.load(locale)
      : GlobalMaterialLocalizations.delegate.load(const Locale('en'));
  @override
  bool shouldReload(covariant LocalizationsDelegate<MaterialLocalizations> old) => false;
}

class FallbackCupertinoLocalizationsDelegate extends LocalizationsDelegate<CupertinoLocalizations> {
  const FallbackCupertinoLocalizationsDelegate();
  @override
  bool isSupported(Locale locale) => true;
  @override
  Future<CupertinoLocalizations> load(Locale locale) => GlobalCupertinoLocalizations.delegate.isSupported(locale)
      ? GlobalCupertinoLocalizations.delegate.load(locale)
      : GlobalCupertinoLocalizations.delegate.load(const Locale('en'));
  @override
  bool shouldReload(covariant LocalizationsDelegate<CupertinoLocalizations> old) => false;
}

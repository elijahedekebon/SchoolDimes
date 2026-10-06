import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';
import 'app/providers.dart';
import 'features/notifications/push.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  final cache = await createDashboardCache();
  runApp(ProviderScope(
    overrides: [dashboardCacheProvider.overrideWithValue(cache)],
    child: const PushRegistrar(child: ParentApp()),
  ));
}

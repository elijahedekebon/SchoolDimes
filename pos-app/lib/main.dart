import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import 'app/app.dart';
import 'features/sync/background_sync.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  try {
    await registerBackgroundSync();
  } catch (_) {
    // background sync is a bonus; foreground triggers still run
  }
  runApp(const ProviderScope(child: PosApp()));
}

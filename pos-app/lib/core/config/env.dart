import 'package:flutter/services.dart' show appFlavor;

/// Build configuration. Everything here is a compile-time constant, so
/// dev-only code guarded by [Env.isDev] is tree-shaken out of prod builds.
abstract final class Env {
  /// `flutter run --flavor dev|prod` (Android product flavors).
  static const String flavor = appFlavor ?? 'dev';
  static const bool isDev = appFlavor != 'prod';

  /// Backend origin, e.g. `--dart-define=API_BASE_URL=http://192.168.1.20:8000`.
  /// Emulator default: the host machine is 10.0.2.2.
  static const String defaultApiBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: isDev ? 'http://10.0.2.2:8000' : '');

  static const String appVersion = String.fromEnvironment('APP_VERSION', defaultValue: '0.1.0');

  /// Warn staff when the offline cache is older than this.
  static const Duration cacheStaleAfter = Duration(hours: 6);

  /// Sync tuning (overridable in settings).
  static const int syncBatchSize = 100;
  static const Duration syncInterval = Duration(minutes: 2);
  static const Duration cacheRefreshInterval = Duration(minutes: 10);
  static const Duration syncedRetention = Duration(days: 30);
  static const Duration attendanceDedupWindow = Duration(seconds: 60);
  static const Duration onlineTimeout = Duration(seconds: 8);
}

import 'package:flutter/services.dart' show appFlavor;

/// Build configuration (compile-time constants, like the POS app).
abstract final class Env {
  static const String flavor = appFlavor ?? 'dev';
  static const bool isDev = appFlavor != 'prod';

  /// Backend origin: --dart-define=API_BASE_URL=http://10.0.2.2:8000
  static const String apiBaseUrl =
      String.fromEnvironment('API_BASE_URL', defaultValue: isDev ? 'http://10.0.2.2:8000' : 'https://api.schooldimes.example');

  static const String appVersion = String.fromEnvironment('APP_VERSION', defaultValue: '0.1.0');

  /// Real push (FCM) needs a Firebase project + google-services.json; until
  /// then only the token-registration code path exists behind this flag.
  static const bool pushEnabled = bool.fromEnvironment('PUSH_ENABLED');

  static const Duration depositPollEvery = Duration(seconds: 3);
  static const Duration depositPollFor = Duration(minutes: 3);
}

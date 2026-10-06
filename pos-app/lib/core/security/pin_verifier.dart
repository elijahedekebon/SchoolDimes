import 'dart:convert';
import 'dart:isolate';

import 'package:flutter/services.dart';

import 'pbkdf2.dart';

/// Verifies a PIN against the cached Django hash, on the device. The raw PIN
/// is never stored, logged or sent anywhere by this class.
///
/// Default: the pure-Dart implementation (AOT-compiled) in a background
/// isolate. Measured on the same Android device in a profile build it is ~4x
/// FASTER than Android's own PBKDF2WithHmacSHA256 (1.4 s vs 5.7 s for 870k
/// iterations), so the native method channel is kept only as an option.
class PinVerifier {
  PinVerifier({MethodChannel? channel, this.preferNative = false})
      : _channel = channel ?? const MethodChannel('ug.schooldimes.pos/pbkdf2');

  final MethodChannel _channel;
  final bool preferNative;

  /// `null` when the hash isn't a scheme the device can check offline (the
  /// card is then online-only, per the API contract).
  static bool canVerifyOffline(String? encoded) =>
      encoded != null && encoded.startsWith(r'pbkdf2_sha256$') && encoded.split(r'$').length == 4;

  Future<bool> verify(String pin, String encoded) async {
    if (!canVerifyOffline(encoded)) return false;
    if (preferNative) {
      try {
        final parts = encoded.split(r'$');
        final out = await _channel.invokeMethod<Uint8List>('derive', {
          'password': pin,
          'salt': parts[2],
          'iterations': int.parse(parts[1]),
          'keyLengthBits': 256,
        });
        if (out != null) {
          return verifyDjangoPbkdf2(pin, encoded, derive: (_, _, _) => out);
        }
      } on MissingPluginException {
        // not on Android (or in tests): fall through to Dart
      } on PlatformException {
        // native failure: fall through to Dart
      }
    }
    return Isolate.run(() => verifyDjangoPbkdf2(pin, encoded));
  }

  /// Synchronous Dart path (tests / background isolates).
  static bool verifyDart(String pin, String encoded) => verifyDjangoPbkdf2(pin, encoded);

  static List<int> utf8Bytes(String s) => utf8.encode(s);
}

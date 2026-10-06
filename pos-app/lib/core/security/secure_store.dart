import 'dart:convert';
import 'dart:math';

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

import 'pbkdf2.dart';

/// Small key/value secret store (Android Keystore-backed in the app,
/// in-memory in tests).
abstract class SecretStore {
  Future<String?> read(String key);
  Future<void> write(String key, String? value);
}

class PlatformSecretStore implements SecretStore {
  const PlatformSecretStore();
  static const _s = FlutterSecureStorage();
  @override
  Future<String?> read(String key) => _s.read(key: key);
  @override
  Future<void> write(String key, String? value) => value == null ? _s.delete(key: key) : _s.write(key: key, value: value);
}

class MemorySecretStore implements SecretStore {
  final Map<String, String> data = {};
  @override
  Future<String?> read(String key) async => data[key];
  @override
  Future<void> write(String key, String? value) async => value == null ? data.remove(key) : data[key] = value;
}

String randomHex(int bytes) {
  final r = Random.secure();
  return List.generate(bytes, (_) => r.nextInt(256).toRadixString(16).padLeft(2, '0')).join();
}

/// Local staff/admin PIN: PBKDF2 like the backend (fewer iterations: it
/// only guards the settings screen of one device).
String hashAdminPin(String pin) {
  final salt = randomHex(12);
  const iterations = 60000;
  return 'pbkdf2_sha256\$$iterations\$$salt\$${base64.encode(pbkdf2Sha256(utf8.encode(pin), utf8.encode(salt), iterations))}';
}

bool checkAdminPin(String pin, String encoded) => verifyDjangoPbkdf2(pin, encoded);

import 'package:flutter_secure_storage/flutter_secure_storage.dart';

/// JWTs live only in the platform keystore (flutter_secure_storage).
abstract class TokenStore {
  Future<String?> access();
  Future<String?> refresh();
  Future<void> save(String access, String refresh);
  Future<void> clear();
}

class SecureTokenStore implements TokenStore {
  const SecureTokenStore();
  static const _s = FlutterSecureStorage();
  @override
  Future<String?> access() => _s.read(key: 'access');
  @override
  Future<String?> refresh() => _s.read(key: 'refresh');
  @override
  Future<void> save(String access, String refresh) async {
    await _s.write(key: 'access', value: access);
    await _s.write(key: 'refresh', value: refresh);
  }

  @override
  Future<void> clear() async {
    await _s.delete(key: 'access');
    await _s.delete(key: 'refresh');
  }
}

class MemoryTokenStore implements TokenStore {
  String? a, r;
  @override
  Future<String?> access() async => a;
  @override
  Future<String?> refresh() async => r;
  @override
  Future<void> save(String access, String refresh) async {
    a = access;
    r = refresh;
  }

  @override
  Future<void> clear() async => a = r = null;
}

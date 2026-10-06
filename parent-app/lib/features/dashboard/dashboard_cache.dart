import 'dart:convert';
import 'dart:io';

/// Last good /parent/dashboard/ response, for read-only viewing offline.
class DashboardCache {
  DashboardCache(this.dir);
  final Directory dir;
  File get _file => File('${dir.path}/dashboard_cache.json');

  Future<void> save(Map<String, dynamic> dashboard, {DateTime? at}) async {
    await dir.create(recursive: true);
    await _file.writeAsString(jsonEncode({'saved_at': (at ?? DateTime.now()).toUtc().toIso8601String(), 'data': dashboard}));
  }

  Future<(Map<String, dynamic>, DateTime)?> load() async {
    if (!await _file.exists()) return null;
    try {
      final j = jsonDecode(await _file.readAsString()) as Map;
      return ((j['data'] as Map).cast<String, dynamic>(), DateTime.parse(j['saved_at'] as String));
    } catch (_) {
      return null;
    }
  }

  Future<void> clear() async {
    if (await _file.exists()) await _file.delete();
  }
}

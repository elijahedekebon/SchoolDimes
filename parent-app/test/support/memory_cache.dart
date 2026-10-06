import 'dart:io';

import 'package:schooldimes_parent/features/dashboard/dashboard_cache.dart';

/// In-memory DashboardCache: real file I/O never completes inside
/// testWidgets' fake-async zone.
class MemoryDashboardCache extends DashboardCache {
  MemoryDashboardCache() : super(Directory.systemTemp);
  (Map<String, dynamic>, DateTime)? _v;

  @override
  Future<void> save(Map<String, dynamic> dashboard, {DateTime? at}) async => _v = (dashboard, (at ?? DateTime.now()).toUtc());
  @override
  Future<(Map<String, dynamic>, DateTime)?> load() async => _v;
  @override
  Future<void> clear() async => _v = null;
}

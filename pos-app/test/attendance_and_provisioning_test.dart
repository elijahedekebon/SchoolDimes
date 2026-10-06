import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_pos/core/api/api_client.dart';
import 'package:schooldimes_pos/core/db/database.dart';
import 'package:schooldimes_pos/core/security/secure_store.dart';
import 'package:schooldimes_pos/features/attendance/attendance_service.dart';
import 'package:schooldimes_pos/features/cache/cache_service.dart';
import 'package:schooldimes_pos/features/provisioning/device_config.dart';
import 'package:schooldimes_pos/features/provisioning/provisioning_service.dart';
import 'package:schooldimes_pos/features/sync/sync_engine.dart';

import 'support/fake_api.dart';

void main() {
  late AppDatabase db;
  late FakePosApi api;

  setUp(() async {
    db = memoryDatabase();
    api = FakePosApi()
      ..rosterPayload = {
        'generated_at': '2026-10-05T07:00:00+00:00',
        'full': true,
        'cards': [
          {'card_uid': '04aa', 'status': 'active', 'student_id': 1, 'student_display_name': 'Amina Nakato', 'class_name': 'P4', 'photo_url': null},
          {'card_uid': '04bb', 'status': 'lost', 'student_id': 2, 'student_display_name': 'Brian Okello', 'class_name': 'P2', 'photo_url': null},
          {'card_uid': '04cc', 'status': 'frozen', 'student_id': 3, 'student_display_name': 'Cynthia Auma', 'class_name': 'P6', 'photo_url': null},
        ],
      };
    await CacheService(db, api).refreshRoster(full: true);
  });
  tearDown(() => db.close());

  group('attendance', () {
    test('a tap is queued with the student name; duplicates within the window are ignored', () async {
      final svc = AttendanceService(db);
      final t0 = DateTime.utc(2026, 10, 5, 4, 30);
      expect((await svc.tap('04aa', 'in', now: t0)).status, TapStatus.recorded);
      expect((await svc.tap('04aa', 'in', now: t0.add(const Duration(seconds: 20)))).status, TapStatus.duplicateIgnored);
      expect((await svc.tap('04aa', 'out', now: t0.add(const Duration(seconds: 25)))).status, TapStatus.recorded);
      expect((await svc.tap('04aa', 'in', now: t0.add(const Duration(minutes: 5)))).status, TapStatus.recorded);
      expect((await db.select(db.attendanceQueue).get()).map((r) => r.studentName).toSet(), {'Amina Nakato'});
    });

    test('unknown and lost cards are refused; a frozen card can still tap in (no money moves)', () async {
      final svc = AttendanceService(db);
      expect((await svc.tap('ffff', 'in')).status, TapStatus.unknownCard);
      expect((await svc.tap('04bb', 'in')).status, TapStatus.lostCard);
      expect((await svc.tap('04cc', 'in')).status, TapStatus.recorded);
    });

    test('taps survive a network failure and sync once', () async {
      final svc = AttendanceService(db);
      await svc.tap('04aa', 'in');
      await svc.tap('04cc', 'in');
      final sync = SyncEngine(db: db, api: api, canSell: false, canRecordAttendance: true);
      api.failNextTaps = ApiException(network: true);
      await sync.run(manual: true, refreshCache: false);
      expect((await db.select(db.attendanceQueue).get()).every((t) => t.status == 'pending'), isTrue);
      final r = await sync.run(manual: true, refreshCache: false);
      expect(r.tapsCreated, 2);
      expect(api.tapCalls[0].map((t) => t['idempotency_key']), api.tapCalls[1].map((t) => t['idempotency_key']));
      expect((await db.select(db.attendanceQueue).get()).every((t) => t.status == 'created'), isTrue);
    });
  });

  group('provisioning', () {
    test('parses the dashboard QR and rejects anything else', () {
      final c = ProvisioningCode.parse('{"type":"schooldimes_device","v":1,"api_base_url":"http://192.168.1.20:8000/","device_token":"q3X9aB1cq3X9aB1cq3X9aB1cq3X9aB1cq3X9aB1cq3X"}');
      expect(c!.apiBaseUrl, 'http://192.168.1.20:8000');
      expect(ProvisioningCode.parse('hello'), isNull);
      expect(ProvisioningCode.parse('{"type":"other","v":1}'), isNull);
      expect(ProvisioningCode.parse('{"type":"schooldimes_device","v":1,"api_base_url":"ftp://x","device_token":"aaaaaaaaaaaaaaaaaaaaaaaaa"}'), isNull);
    });

    PosApi okApi(int id, {ApiException? fail}) => _DeviceApi(id, fail);

    test('validates the token with /pos/device/ and stores the identity in secure storage', () async {
      final store = MemorySecretStore();
      final svc = ProvisioningService(store, (url, token) => okApi(7));
      final cfg = await svc.provision(baseUrl: 'http://10.0.2.2:8000/', token: 'tok', adminPin: '9999', db: db);
      expect(cfg.deviceId, 7);
      expect(cfg.baseUrl, 'http://10.0.2.2:8000');
      expect((await svc.load())!.role, 'canteen');
      expect(checkAdminPin('9999', cfg.adminPinHash), isTrue);
      expect(await svc.databaseKey(), hasLength(64));
    });

    test('a revoked/invalid token is reported as such', () async {
      final svc = ProvisioningService(MemorySecretStore(), (url, token) => okApi(7, fail: ApiException(statusCode: 401)));
      await expectLater(svc.provision(baseUrl: 'http://x', token: 't', adminPin: '1', db: db),
          throwsA(isA<ProvisioningError>().having((e) => e.code, 'code', 'invalid_token')));
    });

    test('switching to a different device is refused while unsynced records exist', () async {
      final store = MemorySecretStore();
      await ProvisioningService(store, (u, t) => okApi(7)).provision(baseUrl: 'http://x', token: 't', adminPin: '1', db: db);
      await AttendanceService(db).tap('04aa', 'in');
      final svc = ProvisioningService(store, (u, t) => okApi(8));
      await expectLater(svc.provision(baseUrl: 'http://x', token: 't2', adminPin: '1', db: db),
          throwsA(isA<ProvisioningError>().having((e) => e.code, 'code', 'unsynced_other_device')));
      // rotating THIS device's token is fine
      await ProvisioningService(store, (u, t) => okApi(7)).provision(baseUrl: 'http://x', token: 't3', adminPin: '', db: db);
      expect((await svc.load())!.token, 't3');
    });

    test('prod requires https', () async {
      final svc = ProvisioningService(MemorySecretStore(), (u, t) => okApi(7), requireHttps: true);
      await expectLater(svc.provision(baseUrl: 'http://x', token: 't', adminPin: '1', db: db),
          throwsA(isA<ProvisioningError>().having((e) => e.code, 'code', 'https_required')));
    });
  });
}

class _DeviceApi extends FakePosApi {
  _DeviceApi(this.id, this.fail);
  final int id;
  final ApiException? fail;
  @override
  Future<Map<String, dynamic>> device() async {
    if (fail != null) throw fail!;
    return {
      'id': id,
      'device_name': 'Till',
      'device_role': 'canteen',
      'status': 'active',
      'school': {'id': 1, 'name': 'Kampala Demo', 'supported_languages': ['en', 'lg'], 'default_language': 'en'},
      'merchant': null,
      'settings': {'offline_spend_ceiling': '2000.00', 'pin_lockout_threshold': 5, 'attendance_on_canteen_devices': false},
      'can_sell': true,
      'can_record_attendance': false,
      'can_p2p': true,
    };
  }
}

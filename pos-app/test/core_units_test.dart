import 'dart:typed_data';

import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_pos/core/money/money.dart';
import 'package:schooldimes_pos/core/nfc/uid.dart';
import 'package:schooldimes_pos/core/time/kampala.dart';

void main() {
  group('card UID normalisation (must equal the backend)', () {
    test('reader bytes -> lowercase hex in reader order', () {
      expect(uidFromBytes(Uint8List.fromList([0x04, 0xA2, 0x2B, 0x7C, 0x91, 0x3E, 0x80])), '04a22b7c913e80');
    });
    test('typed input forms', () {
      expect(normalizeUid('04:A2:2B:7C:91:3E:80'), '04a22b7c913e80');
      expect(normalizeUid(' 04 a2 2b 7c '), '04a22b7c');
      expect(normalizeUid('04-A2-2B-7C'), '04a22b7c');
      expect(normalizeUid('45eb3e68775a49aea1f0ec9c0406bea8'), '45eb3e68775a49aea1f0ec9c0406bea8');
    });
    test('rejects what the backend rejects', () {
      for (final bad in ['', '04a2', '04a22b7', 'zz112233', '04:a2:2b:7c:9']) {
        expect(normalizeUid(bad), isNull, reason: bad);
      }
    });
  });

  group('Money', () {
    test('parses and prints API strings', () {
      expect(Money.parse('5000').toApi(), '5000.00');
      expect(Money.parse('1500.5').cents, 150050);
      expect(Money.parse('-12.00').format(), '-UGX 12');
      expect(Money.parse('15000.00').format(), 'UGX 15,000');
      expect(Money.parse('1500.50').format(), 'UGX 1,500.50');
      expect(Money.tryParse('1.234'), isNull);
    });
    test('arithmetic is exact', () {
      expect((Money.parse('0.10') + Money.parse('0.20')).toApi(), '0.30');
      expect((Money.parse('500') * 3).toApi(), '1500.00');
    });
  });

  group('Kampala time (UTC+3, no DST)', () {
    test('day boundary', () {
      expect(Kampala.day(DateTime.utc(2026, 10, 4, 20, 59)), '2026-10-04');
      expect(Kampala.day(DateTime.utc(2026, 10, 4, 21, 0)), '2026-10-05');
    });
    test('week starts on Monday', () {
      expect(Kampala.weekStart(DateTime.utc(2026, 10, 7, 9)), '2026-10-05'); // Wednesday
      expect(Kampala.weekStart(DateTime.utc(2026, 10, 4, 22)), '2026-10-05'); // Sunday 22:00 UTC = Monday 01:00 Kampala
    });
    test('device_local_timestamp format', () {
      expect(Kampala.isoLocal(DateTime.utc(2026, 9, 30, 6, 15, 2)), '2026-09-30T09:15:02+03:00');
    });
  });
}

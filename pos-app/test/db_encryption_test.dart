import 'dart:io';

import 'package:drift/drift.dart' show Value;
import 'package:flutter_test/flutter_test.dart';
import 'package:schooldimes_pos/core/db/database.dart';
import 'package:sqlite3/sqlite3.dart';

const key = '0f1e2d3c4b5a69788796a5b4c3d2e1f00f1e2d3c4b5a69788796a5b4c3d2e1f0';

void main() {
  late Directory dir;
  setUp(() => dir = Directory.systemTemp.createTempSync('sdpos'));
  tearDown(() => dir.deleteSync(recursive: true));

  test('the database file is encrypted at rest and only opens with the key', () async {
    final file = File('${dir.path}/pos.db');
    final db = AppDatabase(openEncrypted(file, key));
    await db.setKv('secret', 'pbkdf2_sha256\$870000\$salt\$hash');
    await db.close();

    expect(file.readAsBytesSync().length, greaterThan(0));
    expect(String.fromCharCodes(file.readAsBytesSync()).contains('pbkdf2_sha256'), isFalse);
    expect(String.fromCharCodes(file.readAsBytesSync()).startsWith('SQLite format 3'), isFalse);

    // no key -> not a database
    final raw = sqlite3.open(file.path);
    expect(() => raw.select('SELECT * FROM kv'), throwsA(isA<SqliteException>()));
    raw.close();

    // wrong key -> refused
    final wrong = AppDatabase(openEncrypted(file, 'ff' * 32));
    await expectLater(wrong.getKv('secret'), throwsA(anything));
    await wrong.close();

    // right key -> data back
    final again = AppDatabase(openEncrypted(file, key));
    expect(await again.getKv('secret'), startsWith('pbkdf2_sha256'));
    await again.close();
  });

  test('queue rows survive closing and reopening the app', () async {
    final file = File('${dir.path}/q.db');
    var db = AppDatabase(openEncrypted(file, key));
    await db.into(db.saleQueue).insert(SaleQueueCompanion.insert(
          idempotencyKey: 'k-1', cardUid: '04aa', studentName: 'A', amountCents: 150000, itemsJson: '[]',
          deviceLocalTimestamp: '2026-10-05T10:00:00+03:00', kampalaDay: '2026-10-05', kampalaWeek: '2026-10-05',
          createdAt: DateTime.utc(2026, 10, 5, 7), channel: 'offline', status: 'pending', flags: const Value(''),
        ));
    await db.close();
    db = AppDatabase(openEncrypted(file, key));
    final rows = await db.select(db.saleQueue).get();
    expect(rows.single.status, 'pending');
    expect(rows.single.amountCents, 150000);
    await db.close();
  });
}

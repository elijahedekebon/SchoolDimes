// Times the on-device PIN check. Run in PROFILE mode (optimised, like the
// shipped app); debug builds interpret Android's crypto and are ~10x slower:
//   flutter drive --profile --flavor dev --driver=test_driver/integration_test.dart \
//     --target=integration_test/pin_speed_test.dart -d <device>
import 'package:flutter_test/flutter_test.dart';
import 'package:integration_test/integration_test.dart';
import 'package:schooldimes_pos/core/security/pbkdf2.dart';
import 'package:schooldimes_pos/core/security/pin_verifier.dart';

const vector = r'pbkdf2_sha256$870000$Zp1sAltValue0001$QjRoWpfHmhZknMcby7lVqmy5XHN+EwrR+Avul8TiC08=';

void main() {
  IntegrationTestWidgetsFlutterBinding.ensureInitialized();
  testWidgets('PIN check speed: native vs Dart', (t) async {
    var sw = Stopwatch()..start();
    expect(await PinVerifier(preferNative: true).verify('1234', vector), isTrue);
    final native = sw.elapsedMilliseconds;
    sw = Stopwatch()..start();
    expect(verifyDjangoPbkdf2('1234', vector), isTrue);
    final dart = sw.elapsedMilliseconds;
    // ignore: avoid_print
    print('PIN_SPEED native=${native}ms dart=${dart}ms');
  });
}

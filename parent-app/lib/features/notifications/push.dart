import 'package:flutter/widgets.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

import '../../app/providers.dart';
import '../../core/config/env.dart';

/// Push token registration (POST/DELETE /notifications/push-tokens/).
///
/// Real delivery needs Firebase Cloud Messaging: a Firebase project, the
/// app's google-services.json and the firebase_messaging plugin (see
/// parent-app/README.md "Enabling push"). Until then this is off
/// (`--dart-define=PUSH_ENABLED=true` turns it on) and the in-app inbox is
/// the working channel.
abstract interface class PushTokenSource {
  Future<String?> token();
}

/// Replace with a FirebaseMessaging-backed source once FCM is configured.
class NoPushTokenSource implements PushTokenSource {
  const NoPushTokenSource();
  @override
  Future<String?> token() async => null;
}

final pushTokenSourceProvider = Provider<PushTokenSource>((ref) => const NoPushTokenSource());

class PushRegistrar extends ConsumerWidget {
  const PushRegistrar({super.key, required this.child});
  final Widget child;
  @override
  Widget build(BuildContext context, WidgetRef ref) {
    if (Env.pushEnabled) {
      ref.listen(authProvider, (prev, next) async {
        if (next.value?.signedIn == true && prev?.value?.signedIn != true) {
          final t = await ref.read(pushTokenSourceProvider).token();
          if (t != null) await ref.read(parentApiProvider).registerPushToken(t, 'android');
        }
      });
    }
    return child;
  }
}

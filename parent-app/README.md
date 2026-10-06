# SchoolDimes parent app

Flutter app for parents: every linked child's balances, savings and card,
itemized history, top-ups (mobile money / USSD / bank), automatic top-ups,
gifts and links for relatives, class funds, spending limits, savings goals
and withdrawals, card freeze, P2P oversight, disputes, notifications and
privacy. All data comes from the backend (`docs/PARENT_APP_READINESS.md`).

Same structure and conventions as `pos-app/` (Riverpod, feature-first,
ARB en/lg/sw, dev/prod flavors).

## Run it

```bash
# backend (repo root)
docker compose up -d && docker compose exec web python manage.py seed_demo

cd parent-app
flutter pub get
flutter run --flavor dev --dart-define=API_BASE_URL=http://10.0.2.2:8000        # emulator
flutter run --flavor dev --dart-define=API_BASE_URL=http://<PC LAN IP>:8000     # phone on the same Wi-Fi
```

Sign in as `parent1@schooldimes.test` / `pw123456` (two children), or
create a new account (the school then links children to it from the
dashboard). Confirm a top-up in mock mode with
`docker compose exec web python manage.py mock_webhook <reference>`; the
reference is shown on the payment screen.

| Flavor | Network | App id |
|---|---|---|
| dev | cleartext HTTP to the LAN backend allowed | `ug.schooldimes.schooldimes_parent.dev` |
| prod | HTTPS only | `ug.schooldimes.schooldimes_parent` |

Build defines: `API_BASE_URL`, `APP_VERSION`, `PUSH_ENABLED`.

## Running on a physical phone

1. Phone and PC on the same Wi-Fi; find the PC's IP (macOS
   `ipconfig getifaddr en0`).
2. Enable USB debugging, connect, `flutter devices`.
3. `flutter run --flavor dev -d <id> --dart-define=API_BASE_URL=http://<IP>:8000`.

## Enabling push notifications (FCM)

The in-app inbox works without this. To add real push:

1. Create a Firebase project; add an Android app with id
   `ug.schooldimes.schooldimes_parent` (and `.dev`); download
   `google-services.json` into `android/app/` (one per flavor under
   `android/app/src/<flavor>/` if the ids differ).
2. Add the Google services Gradle plugin (`com.google.gms.google-services`)
   to `android/settings.gradle.kts` and `android/app/build.gradle.kts`.
3. `flutter pub add firebase_core firebase_messaging`; call
   `Firebase.initializeApp()` in `main()`.
4. Implement `PushTokenSource` with `FirebaseMessaging.instance.getToken()`
   and override `pushTokenSourceProvider` in `main()`. On notification
   taps, call `openDeepLink(context, ref, deepLinkFor(type, payload))`.
5. Backend: set `PUSH_BACKEND` and the FCM credentials (`FCM_PROJECT_ID`,
   `FCM_SERVICE_ACCOUNT_FILE`, see `backend/.env.example`).
6. Build with `--dart-define=PUSH_ENABLED=true`.

## Tests

```bash
flutter test                              # unit + widget tests (~5 s)
tool/run_integration.sh emulator-5554     # real app vs backend: login → dashboard → top-up →
                                          # mock_webhook → balance updated
```

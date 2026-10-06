# SchoolDimes POS app

One Flutter app for the school's terminals. The role is set when the device
is registered in the dashboard:

| Role | What the device does |
|---|---|
| **canteen** | sells canteen products; student-to-student transfers (card + PIN, online only); attendance taps too if the school enables it |
| **merchant** | sells one approved nearby merchant's products |
| **attendance** | gate reader: tap in / tap out, no PIN, no money |

Android first (NFC); iOS is kept buildable but untested.

## Run it

```bash
# backend (repo root)
docker compose up -d && docker compose exec web python manage.py seed_demo

cd pos-app
flutter pub get
# emulator (host machine is 10.0.2.2)
flutter run --flavor dev --dart-define=API_BASE_URL=http://10.0.2.2:8000
# phone on the same Wi-Fi as the PC
flutter run --flavor dev --dart-define=API_BASE_URL=http://<PC LAN IP>:8000
```

The backend's `ALLOWED_HOSTS` must include the address you use (the dev
default is `*`). Real-device steps: `docs/POS_DEVICE_TESTING.md`.

### Flavors

| | dev | prod |
|---|---|---|
| App id | `ug.schooldimes.schooldimes_pos.dev` | `ug.schooldimes.schooldimes_pos` |
| Network | cleartext HTTP allowed (LAN backend) | HTTPS only |
| Backend address | editable on the setup screen | from the QR code / `API_BASE_URL` |
| Dev tools | "simulate tap" (type a UID), "show card UID" | removed at compile time |

Build defines: `API_BASE_URL`, `APP_VERSION`, `SYNC_INTERVAL_SECONDS`
(default 120).

## Setting up a device

1. Dashboard → **Devices → Register device** (or a merchant's row → register
   device). The token and a QR code are shown **once**.
2. On the device: **Scan QR code** (or type the token), choose a staff PIN
   (protects settings), **Set up device**. The app checks the token with
   `GET /pos/device/` and downloads the cards/products (or the gate roster)
   before the home screen appears.

If the school revokes or rotates the token, the device stops selling,
keeps its unsynced records and asks to be set up again.

## How a sale works (offline-first)

1. Staff tap products (or **Custom amount**) → **Charge**.
2. The student taps their card. Frozen, lost, unknown or locked cards are
   refused with no PIN prompt.
3. The student enters their PIN, verified **on the device** against the
   cached hash. Wrong PINs are counted; at the school's limit the card is
   locked on this device and reported on the next sync (the server freezes
   it).
4. The app runs the same checks as the server (`card_frozen`,
   `insufficient_funds` within the offline spend ceiling, per-transaction /
   daily / weekly caps, blocked or not-allowed categories, blocked items,
   blocked merchant).
5. Staff confirm. The sale is written to the encrypted local queue first,
   then sent to `POST /pos/purchase/`. If the server refuses, nothing
   happened. If there's no answer, the sale stays queued with the same
   idempotency key and goes out with the next sync: it can never be charged
   twice.
6. The receipt shows items, total and the new balance (marked "estimated"
   and "Offline — will sync" when offline).

Sync runs on start-up, when the network comes back, every 2 minutes, a few
seconds after each offline record, on **Sync now**, and in the background
(WorkManager). Server results go to **Staff → Needs review / Rejected**;
the school resolves them in the dashboard.

## Staff area

Behind the staff PIN (or the staff member's fingerprint): today's sales and
taps (synced vs pending), needs-review and rejected lists, language, sync
now, refresh card data, locked cards (unlock), device info, set up again,
and in dev builds **Show card UID**.

## Tests

```bash
flutter test                         # unit + DB + sync + policy engine + PIN vectors (~10 s)
SD_LIVE=1 flutter test test/live     # against the running backend (host)
tool/run_integration.sh emulator-5554  # the real app on an emulator/device
flutter drive --profile --flavor dev --driver=test_driver/integration_test.dart \
  --target=integration_test/pin_speed_test.dart -d <device>   # PIN check speed
```

`test/policy_engine_test.dart` mirrors `backend/policies/tests.py` case for
case; `test/pin_vectors_test.dart` uses hashes produced by the backend's own
`make_password`.

## Layout

```
lib/
  app/        session (identity + encrypted DB + API), providers, shell
  core/       api, config, db (drift), l10n (ARB en/lg/sw), money, nfc, security, time, ui
  features/   provisioning, cache, policy, sale, p2p, attendance, sync, staff
```

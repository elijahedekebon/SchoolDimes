# Part 3 Plan — POS app (`pos-app/`)

One Flutter app for the three device roles (canteen, merchant, attendance).
If a session is interrupted: re-read this file and `git log`, continue from
the first unticked section. Each section ends with: tests green → tick →
README updated → commit `Part 3 – Section X: ...`.

## Decisions (recorded in DECISIONS.md)

| Concern | Choice |
|---|---|
| State | Riverpod 3 (`flutter_riverpod`, no codegen): `Provider` for services, `Notifier`/`AsyncNotifier` for screen state |
| Structure | feature-first: `lib/core/{api,db,security,nfc,money,time,config,l10n}`, `lib/features/{provisioning,cache,sale,p2p,attendance,sync,staff}` |
| HTTP | `dio`, one `ApiClient` (device-token header, `X-App-Version`, `Accept-Language`, timeouts, `{code, detail}` → `ApiException`) |
| Local DB | `drift` on `sqlite3` 3.x with the **SQLite3MultipleCiphers** build (`hooks.user_defines.sqlite3.source: sqlite3mc`), `PRAGMA key` from a random 256-bit key in `flutter_secure_storage` |
| Money | `Money` = integer cents (`int`), parsed from/printed to the API's decimal strings; never `double` |
| Time | Africa/Kampala = fixed UTC+3 (no DST); device timestamps sent as ISO-8601 with `+03:00` |
| PIN | Django `pbkdf2_sha256` verified on-device: Android native `PBKDF2WithHmacSHA256` via a method channel, pure-Dart fallback; both tested against vectors made by the backend's own `make_password` |
| Flavors | `dev` / `prod` Android product flavors; dev-only tools guarded by `appFlavor == 'dev'` (compile-time constant, tree-shaken from prod) |

## Contract gaps found and filled (backend, additive — see DECISIONS.md)

1. Attendance devices get `403` on `/pos/cache/`, so a gate couldn't show
   names offline → **`GET /attendance/roster/?since=`** (names, class, photo,
   card status; no PIN hashes or balances).
2. No way for a device (esp. attendance) to validate its token and learn its
   school/merchant/language at provisioning → **`GET /pos/device/`**.
3. The cache had no week-to-date spend, so `weekly_spend_cap` couldn't be
   checked offline → **`week_spend`** per card + `week_start` in `/pos/cache/`.
4. `POST /pos/p2p-transfer/` requires the raw PIN (server-verified). The app
   still verifies locally first; the PIN is sent only for this online-only
   flow, over TLS in prod. Logged as a known tension with "the raw PIN never
   leaves the device".

## Sections

### [x] A. Scaffold & platform setup
- flavors dev/prod, `--dart-define=API_BASE_URL`, app name/icon placeholders
- Android: NFC permission + feature, INTERNET, dev-only network security config (cleartext to LAN), prod HTTPS only
- wakelock in sale/attendance mode, portrait lock
- Tests: config defaults

### [x] B. Device provisioning
- Setup screen: QR scan (dashboard payload `{"type":"schooldimes_device","v":1,"api_base_url","device_token"}`) or manual entry; base URL editable in dev only
- Validate with `GET /pos/device/`; store token, role, school, merchant in secure storage; set local admin PIN
- 401 "Invalid or revoked device token." → lock transacting, keep queue, re-provision screen (rotation = same device id; a different device id is refused while unsynced records exist)
- Tests: QR payload parsing, provisioning service with fake API

### [x] C. Local database & offline cache
- Tables: `cached_cards`, `products`, `categories`, `roster_cards`, `sale_queue`, `attendance_queue`, `pin_failures`, `kv`, `sync_log`
- `CacheService`: full pull on provisioning, `?since=` refresh, apply rules (replace by `card_uid`/`id`, `full_school_ids`), cache-age warning
- Tests: apply full + incremental cache, queue survives reopen

### [x] D. NFC card reading
- `nfc_manager` → UID bytes → `normalizeUid` (lowercase hex, reader order, no separators); NFC off / unsupported / unknown / frozen / lost states
- dev-only "simulate tap" input
- Tests: UID normalisation

### [x] E. PIN verification
- `PinVerifier` (native + Dart), vectors from Django, per-card failure counter + lockout at `pin_lockout_threshold`, reported via sync `pin_failures`
- staff settings: local admin PIN (+ optional `local_auth`); no student biometrics (DECISIONS)
- Tests: vectors, lockout counting

### [x] F. Sale flow
- product grid by category + search, cart, custom amount (allowed: see DECISIONS), card → PIN → local policy checks → confirm → online purchase or offline queue → receipt
- `PolicyEngine` mirroring `debit_violations` (same codes, same order)
- Tests: policy engine per reason code (mirrors backend tests), idempotency key stable across retry

### [x] G. P2P at the terminal (canteen only, online only)
### [x] H. Attendance mode
### [x] I. Sync engine (triggers, batches, per-item results, backoff, pruning, balances → cache)
### [x] J. Staff screens (status bar, today summary, needs-review, rejected, settings)
### [x] K. Localization (en/lg/sw ARB incl. reason codes)
### [x] L. Tests (unit, DB, sync, integration against the running backend on the emulator)
### [x] M. Real-device test guide (`docs/POS_DEVICE_TESTING.md`, `pos-app/README.md`)
### [x] N. Definition of done + summary

## Result

Built: every section A–N. Simplified/not built: receipt printing (no
printer hardware to test), iOS not verified (no Xcode). Tests: 59 unit/DB/
sync/policy/PIN tests (`flutter test`), 2 live-backend tests
(`SD_LIVE=1 flutter test test/live`), 4 on-emulator tests
(`tool/run_integration.sh`). Physical-NFC testing follows
`docs/POS_DEVICE_TESTING.md` (needs a phone with NFC and blank cards).

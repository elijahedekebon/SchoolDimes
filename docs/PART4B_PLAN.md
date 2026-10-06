# Part 4B Plan — Parent app (`parent-app/`)

Client-only part: every screen uses an endpoint listed in
`docs/PARENT_APP_READINESS.md`. If interrupted: re-read this file and
`git log`, continue from the first unticked section.

## Decisions (recorded in DECISIONS.md)

| Concern | Choice |
|---|---|
| Structure / state | Same as `pos-app/`: Riverpod 3 without codegen, feature-first `lib/core/*` + `lib/features/*`, plain-Dart services behind an API interface |
| HTTP / auth | `dio`; JWT access + refresh in `flutter_secure_storage`; one interceptor adds the Bearer token, refreshes once on 401 (single in-flight refresh, rotation-aware) and retries; refresh failure → signed out |
| Shared code | **Not** a shared package: the overlap with the POS app is ~3 small files (Money, Kampala time, API error shape). Copied with a header noting the twin; two independently released apps stay decoupled |
| Money / time | `Money` (int cents, decimal-string API), Africa/Kampala (UTC+3) |
| Offline | last dashboard response cached as JSON in the app support dir, shown read-only with "last updated …" when offline |
| Idempotency | one key per user action (deposit, gift voucher, fund contribution, withdrawal); kept across retries until success |
| Push | token registration behind `--dart-define=PUSH_ENABLED=true`; in-app inbox is the working channel (no Firebase project provided) |
| i18n | ARB en/lg/sw (lg/sw untranslated → English, listed in TRANSLATIONS_TODO) |

## Sections
### [x] A. Scaffold & flavors
### [x] B. Authentication (register, login, logout, refresh, app lock)
### [x] C. Onboarding & KYC-lite
### [x] D. Multi-child dashboard (+ tip, offline cache)
### [x] E. Student detail (history, filters, line items, report a problem)
### [x] F. Top-ups (channels, instructions, polling, history, one-tap from low balance)
### [x] G. Recurring top-ups
### [x] H. Gift vouchers & contributor links
### [x] I. Pooled funds
### [x] J. Spending controls (school limits alongside, tighten only)
### [x] K. Savings (move, goals, window, withdraw, payout status)
### [x] L. Card control & P2P history
### [x] M. Disputes
### [x] N. Notifications (inbox, read, prefs, deep links, push token)
### [x] O. Privacy & account
### [x] P. Tests & documentation

## Result

All sections built. Tests: 12 unit + widget tests (`flutter test`: login,
dashboard, top-up with status polling, freeze, dispute, offline dashboard,
money formatting, deep-link routing, idempotent retry) and the end-to-end
test on an emulator against the running backend
(`tool/run_integration.sh`: login → dashboard → top-up → `mock_webhook`
→ balance updated). Simplified: real FCM push (no Firebase project; the
token-registration path is behind `PUSH_ENABLED`, steps in the README).

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
### [ ] A. Scaffold & flavors
### [ ] B. Authentication (register, login, logout, refresh, app lock)
### [ ] C. Onboarding & KYC-lite
### [ ] D. Multi-child dashboard (+ tip, offline cache)
### [ ] E. Student detail (history, filters, line items, report a problem)
### [ ] F. Top-ups (channels, instructions, polling, history, one-tap from low balance)
### [ ] G. Recurring top-ups
### [ ] H. Gift vouchers & contributor links
### [ ] I. Pooled funds
### [ ] J. Spending controls (school limits alongside, tighten only)
### [ ] K. Savings (move, goals, window, withdraw, payout status)
### [ ] L. Card control & P2P history
### [ ] M. Disputes
### [ ] N. Notifications (inbox, read, prefs, deep links, push token)
### [ ] O. Privacy & account
### [ ] P. Tests & documentation

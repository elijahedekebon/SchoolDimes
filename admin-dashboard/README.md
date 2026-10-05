# SchoolDimes admin dashboard

One Next.js 16 (App Router, TypeScript) app for every web surface of
SchoolDimes:

| Area | Who | Path |
|---|---|---|
| School admin dashboard | `school_admin` | `/school/...` |
| Platform back-office | `platform_admin` | `/platform/...` |
| Student portal (read-only) | `student` (school-issued login) | `/student` |
| Contributor top-up / gift page | anyone with a link, no login | `/give/{token}` |

Parents use the mobile app and canteen/merchant staff use the POS app; the
login page refuses them with a clear message.

## Run it locally

```bash
# 1. backend (repo root) — Docker Desktop must be running
docker compose up --build -d
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py simulate_pos      # sample sales, shortfalls, attendance

# 2. dashboard
cd admin-dashboard
cp .env.example .env.local
npm install
npm run dev                                                  # http://localhost:3000
```

Seed logins (password `pw123456`):

| Role | Email |
|---|---|
| school_admin (Kampala) | `admin@kampaladps.schooldimes.test` |
| school_admin (Jinja) | `admin@jinjadss.schooldimes.test` |
| platform_admin | `platform@schooldimes.test` |
| student portal (Amina) | `student.amina@kampaladps.schooldimes.test` |
| parent (refused here; for the mobile app) | `parent1@schooldimes.test` |

The contributor page for the seeded link is printed by `seed_demo`
(`TOPUP_LINK_TOKEN=…`): open `http://localhost:3000/give/<token>`, pay, then
confirm with `docker compose exec web python manage.py mock_webhook <reference>`.

Until real POS devices exist, sales, shortfalls and attendance come from
`simulate_pos`.

## Environment variables (`.env.local`)

| Variable | Purpose |
|---|---|
| `NEXT_PUBLIC_API_BASE_URL` | Django origin, e.g. `http://localhost:8000`. Used by the server-side proxy and by the public contributor page (browser → API directly). |
| `API_BASE_URL` | Optional different origin for server-side calls (e.g. `http://web:8000` inside Docker). |
| `NEXT_PUBLIC_DEVICE_API_BASE_URL` | Backend address put in the device-provisioning QR code (a LAN IP such as `http://192.168.1.20:8000` so a phone can reach it). Editable per device in the dialog. |
| `NEXT_PUBLIC_SITE_URL` | This dashboard's public URL. The backend's `PUBLIC_TOPUP_BASE_URL` must be `<this>/give`. |
| `COOKIE_SECURE` | `true` behind HTTPS (auth cookies get the `Secure` flag). |

Backend side: add the dashboard origin to `CORS_ALLOWED_ORIGINS` (default
`http://localhost:3000`) — the contributor page calls the public API from the
browser.

## How auth works

The browser never holds a JWT. `/api/auth/login` (a route handler) logs in
against Django and stores the tokens in httpOnly cookies. Pages call
`/api/proxy/<path>`, which forwards to `<API>/api/v1/<path>` with the Bearer
token, refreshes it transparently on expiry (refresh tokens rotate) and
signals "session ended" if the refresh fails. `src/proxy.ts` (Next 16's
middleware) redirects by role; Django still authorises every call.

## Pages

**School (`/school`)**: overview · sales (by day/device/merchant + transactions
with line items) · reconciliation (per device vs ledger, CSV) · review queue
(offline shortfalls & policy flags) · analytics (best-sellers, peak hours,
categories with nutrition flag, per-student) · students (list, create, detail
with guardians/cards/ledger/P2P/attendance/disputes/policy/portal login) ·
guardians & KYC review · cards (issue by NFC UID, freeze, replace, reset PIN) ·
devices (register → token shown once + QR, rotate, revoke, stale) · merchants
(approve/suspend, statement, merchant devices) · products & categories ·
policy & POS settings · staff accounts · fees (categories, pay, history, CSV)
· attendance (daily register, per student, CSV) · pooled funds (log, close,
disburse) · disputes (refund ≤ original, deny) · P2P alerts · data requests ·
financial tips · payment issues.

**Platform (`/platform`)**: schools with stats · onboarding wizard (school,
branding, languages, policy, POS settings, first admin — one transaction) ·
referrals · support (read-only views of any school) · payment issues
(unmatched webhooks, failed payments) · audit log · platform-wide tips.

## Languages

en / lg / sw with next-intl; the locale is a cookie set from the user's
`preferred_language` at login, and the switcher also PATCHes `/me`. `lg.json`
and `sw.json` only contain native-speaker translations (none yet): missing
keys fall back to English and are listed in `docs/TRANSLATIONS_TODO.md`
(regenerate with `python3 scripts/translations-todo.py`). Django's own error
messages come back translated through `Accept-Language`.

## Tests

```bash
npm test          # Vitest: role routing, proxy token refresh, money formatting
npm run e2e       # Playwright, against the running backend + seed data
```

The e2e suite signs in many times a minute; for local runs set
`AUTH_THROTTLE_RATE=100/min` in `backend/.env` (production keeps 10/min).
It covers: every page renders without an error or missing translation; parents
refused; role redirects; the onboarding wizard; the student portal; the
contributor page end to end (pay → `mock_webhook` → balance + parent
notification); and the admin flow (register device → token shown once →
issue card by UID → freeze → refund a dispute → balance changes). The
onboarding test adds an "E2E School <timestamp>" to the dev database each run.

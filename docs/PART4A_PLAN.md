# Part 4A Plan

Web surfaces (admin dashboard, platform back-office, student portal, public
contributor page) plus backend readiness for the Flutter parent app.
If a session is interrupted: re-read this file and `git log`, continue from
the first unticked section. Each section ends with: tests green → tick here →
docs updated → commit `Part 4A – Section X: ...`.

## Stack (recorded in DECISIONS.md)

| Concern | Choice |
|---|---|
| App | `admin-dashboard/` — Next.js (App Router) + React + TypeScript, port 3000 |
| Components | Mantine (core, hooks, form, notifications, modals, dates) |
| Charts | Recharts |
| i18n | next-intl, cookie-based locale (`en`/`lg`/`sw`), no locale in the URL |
| Auth | httpOnly cookies set by Next.js route handlers; the browser only ever calls `/api/proxy/*` on the dashboard origin, which adds the Bearer token, refreshes once on 401 and retries |
| Money | decimal strings from the API; display via a string formatter; no float arithmetic (comparisons/sums in integer cents via BigInt) |
| Tests | Vitest (unit: role routing, API client refresh, money), Playwright (e2e smoke + one flow against the seeded backend) |
| QR | `qrcode.react` |

## Conflicts / Part 1–2 gaps found while reading (resolved additively, logged in DECISIONS.md)

1. `POST /cards/issue/` and `/reissue/` can't take an NFC UID (the service
   can; the serializer doesn't expose it). → optional `card_uid` field,
   normalised by a new `cards.services.normalize_card_uid()`.
2. No PIN reset endpoint. → `POST /cards/{id}/reset-pin/` (school_admin).
3. `GuardianVerification.status` is read-only in the serializer, so admins
   can't actually review KYC. → `POST /guardian-verifications/{id}/review/`
   + `review_notes`, `reviewed_by` fields (additive migration).
4. Part 1 quirk: parents get 403 on `GET /students/{id}/` (DECISIONS.md, Part 2
   "waiting for approval"). Approved in this session ("do everything"):
   detail routes use queryset scoping instead of `IsSameSchoolObject`.
5. Staff can't see their own school's name/branding (`/schools/` is
   platform-only). → `GET /my-school/`.
6. No parent self-registration, no aggregate parent dashboard, no
   student transaction history with line items, no payout status read.
   → added in Section J.
7. No platform_admin in `seed_demo`. → seeded (`platform@schooldimes.test`).
8. `PUBLIC_TOPUP_BASE_URL` pointed at the backend (`:8000/topup`), but the page
   is the dashboard's `/give/{token}`. → default changed to
   `http://localhost:3000/give` (env var, response shape unchanged).

## Sections

### [x] A. Scaffold, auth & layout
- Next.js app, ESLint/Prettier, `.env.example` (`NEXT_PUBLIC_API_BASE_URL`, `API_BASE_URL`)
- Route handlers: `/api/auth/login`, `/api/auth/logout`, `/api/auth/session`, `/api/proxy/[...path]`
- Middleware: role routing (`school_admin` → `/school`, `platform_admin` → `/platform` + `/school` via `?school`, `student` → `/student`, others refused)
- App shell: sidebar, school branding, language switcher (PATCH `/me`), notifications bell (`/notifications/`)
- Backend: `django-cors-headers` (`CORS_ALLOWED_ORIGINS`), login throttle, `GET /my-school/`
- Tests: route protection unit tests, proxy refresh unit test, backend `my-school` + CORS tests

### [x] B. School admin — overview, sales, reconciliation, shortfalls
- `/school` overview: `analytics/sales-summary`, `analytics/reconciliation`, `pos/shortfalls?page_size=1`, `disputes?status=open`, `p2p-alerts?status=open`, `pos/devices?stale=true`, `privacy/data-requests?status=pending`
- `/school/sales`: `analytics/sales-summary`, `pos/transactions`, `pos/transactions/{id}`
- `/school/reconciliation`: `analytics/reconciliation?date=` + CSV
- `/school/shortfalls`: `pos/shortfalls`, `pos/shortfalls/{id}/resolve`

### [x] C. School admin — analytics
- `/school/analytics`: `best-sellers`, `peak-hours`, `category-breakdown`, `students/{id}/spending`

### [x] D. Students, guardians & cards
- `/school/students` (+ create/edit), `/school/students/{id}` (profile, guardians, wallets, goals, cards, ledger, P2P, attendance, disputes, effective policy)
- `/school/guardians` (links + KYC review)
- Card issue/reissue/freeze/unfreeze/lost/reset-pin with UID entry
- Backend: `card_uid` on issue/reissue, `reset-pin`, KYC `review`, `users/lookup`, student detail fix
- Tests: UID normalisation, reset-pin perms, KYC review perms + tenant isolation

### [x] E. Devices, merchants, products & policy
- `/school/devices` (register → one-time token + QR, rotate, revoke, stale)
- `/school/merchants` (approve/suspend, statement, staff link, merchant devices)
- `/school/products` (categories + products)
- `/school/policy` (school default, school settings, overrides list)
- Backend: `GET/POST /users/` (school_admin creates staff in own school; lists own school's staff) so merchant_staff can be created and linked

### [ ] F. Fees, attendance, pooled funds, disputes, P2P alerts, privacy, tips, payment issues
- `/school/fees`, `/school/attendance`, `/school/pooled-funds`, `/school/disputes`, `/school/p2p-alerts`, `/school/privacy`, `/school/tips`, `/school/payment-issues` (`payments/deposits?status=failed|expired`)

### [ ] G. Platform back-office
- `/platform/schools` (+ onboarding wizard), `/platform/referrals`, `/platform/support` (students/devices/transactions by school), `/platform/audit-log`, `/platform/payment-issues`, `/platform/tips`
- Backend: `POST /platform/schools/onboard/`, `GET /platform/schools/stats/`, `GET /audit-logs/`, `GET /payments/unmatched-webhooks/`
- Test: a school onboarded purely via endpoints registers a device, issues a card and takes a simulated sale

### [ ] H. Student portal
- `/student` (balance, goals, recent purchases, tip)
- Backend: `POST|DELETE /students/{id}/portal-account/` (school_admin), `GET /student-portal/me/`
- Tests: student sees only self, other roles refused

### [ ] I. Contributor page
- `/give/[token]` public page (link info, deposit or gift voucher, instructions, status polling)
- `PUBLIC_TOPUP_BASE_URL` default → dashboard; security model confirmed in DECISIONS.md

### [ ] J. Parent-app backend readiness
- `POST /auth/register`, `GET /parent/dashboard/`, `GET /students/{id}/transactions/`, `GET /payments/payouts/`
- `docs/PARENT_APP_READINESS.md`, `docs/requests/parent/*.http`
- Tests for every new endpoint incl. tenant isolation

### [ ] Final — README, TRANSLATIONS_TODO, Playwright flow, summary

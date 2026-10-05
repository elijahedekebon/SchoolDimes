# Web Migration Plan — Next.js → Django templates + HTMX

A **like-for-like port** of everything Part 4A built in `admin-dashboard/`
(Next.js 16 + React + Mantine + Recharts + next-intl) to server-rendered
Django templates + HTMX inside `backend/`. Same pages, same URL paths, same
navigation, same layout, forms, tables, filters, actions and states. Only the
mechanism changes. Recorded in `docs/DECISIONS.md` ("Web migration").

If a session is interrupted: re-read this file and `git log`, continue from
the first unticked section. Each section ends with: its tests green → tick
here → docs updated → commit `Web migration – Section X: ...`.

## Inventory (what Part 4A had built)

Part 4A was **complete** (Sections A–J + Final, commits `4e50fd9`…`ae70c30`):
30 pages, 3 nested layouts, 13 shared components, 858 English UI strings
(`messages/en.json`), **no** lg/sw UI translations (`lg.json`/`sw.json` are
`{}`), 13 Vitest + 8 Playwright tests. So this migration is a full port of
A–I; J (parent-app API) is backend-only and is kept as is.

## Stack (replaces the Part 4A stack table)

| Concern | Next.js (Part 4A) | Django (this migration) |
|---|---|---|
| Rendering | React client components calling `/api/proxy/*` | Django class-based views + templates; views call `<app>/services.py` directly (never the REST API over HTTP) |
| Partial updates | `useApi`/`usePaginated` re-fetch | HTMX 2 (`hx-get` into a region; the page view returns just that region when `HX-Target` names it) |
| Components | Mantine | one hand-written stylesheet `web/core/static/web/css/app.css` reproducing Mantine's look (teal primary, 8 px radius, system font stack, striped tables, light badges, filled active nav) |
| Modals / drawers | Mantine `Modal` / `Drawer` | native `<dialog>` (modal, right-hand drawer, nested drawer) filled by HTMX, ~150 lines of vanilla JS (`web/core/static/web/js/app.js`) |
| Charts | Recharts | Chart.js 4 (vendored), same chart types (bar, horizontal bar, pie) |
| QR | `qrcode.react` (browser) | `segno` (server-side SVG), same payload |
| i18n | next-intl, `NEXT_LOCALE` cookie | Django i18n (`{% translate %}`/`{% blocktranslate %}`), `LocaleMiddleware`, `django_language` cookie; same en/lg/sw; `.po` built by `manage.py build_locale` |
| Auth | JWT in httpOnly cookies via a Next.js proxy | Django session auth (httpOnly session cookie, CSRF on every POST); REST API keeps JWT unchanged |
| Static files | Next.js | WhiteNoise (`whitenoise.middleware.WhiteNoiseMiddleware`), no build step; vendored `htmx.min.js`, `chart.umd.min.js` |
| Tests | Vitest + Playwright | pytest-django + Django test client |
| Process | `npm run dev` on :3000 | the existing `web` container on :8000 (no new service) |

## Django layout (mirrors the Next.js route groups)

```
backend/web/
  core/      app label web_core     ← src/app/layout.tsx, src/components/*, src/lib/*, /login, /api/auth/*
  school/    app label web_school   ← src/app/school/**
  platform/  app label web_platform ← src/app/platform/**   (a top-level "platform" package would shadow Python's stdlib module)
  student/   app label web_student  ← src/app/student/**
  give/      app label web_give     ← src/app/give/[token]/**
  tests/                            ← e2e/*.spec.ts, src/lib/*.test.ts
```

Template paths mirror the route folders: `app/<area>/<route>/page.tsx` →
`web/<area>/templates/<area>/<route>/index.html`; `[id]/page.tsx` →
`detail.html`; `layout.tsx` → `layout.html`; region partials are `_name.html`
next to their page.

## Route-by-route table

All paths are unchanged. "View" names are in `web/<area>/views.py`.

| # | Next.js route / page file | Django URL (same path) | View | Template | Sec | Status |
|---|---|---|---|---|---|---|
| 1 | `/` · `app/page.tsx` | `/` | `core.HomeRedirectView` | — (redirect) | A | ✅ |
| 2 | `/login` · `app/login/page.tsx` | `/login` | `core.LoginView` | `core/login.html` | A | ✅ |
| 3 | `/school` · `app/school/page.tsx` | `/school` | `school.OverviewView` | `school/index.html` | B | ✅ |
| 4 | `/school/sales` · `school/sales/page.tsx` | `/school/sales` | `school.SalesView` | `school/sales/index.html` | B | ✅ |
| 5 | `/school/reconciliation` · `school/reconciliation/page.tsx` | `/school/reconciliation` | `school.ReconciliationView` | `school/reconciliation/index.html` | B | ✅ |
| 6 | `/school/shortfalls` · `school/shortfalls/page.tsx` | `/school/shortfalls` | `school.ShortfallsView` | `school/shortfalls/index.html` | B | ✅ |
| 7 | `/school/analytics` · `school/analytics/page.tsx` | `/school/analytics` | `school.AnalyticsView` | `school/analytics/index.html` | C | ⬜ |
| 8 | `/school/students` · `school/students/page.tsx` | `/school/students` | `school.StudentsView` | `school/students/index.html` | D | ⬜ |
| 9 | `/school/students/[id]` · `school/students/[id]/page.tsx` | `/school/students/<int:id>` | `school.StudentDetailView` | `school/students/detail.html` | D | ⬜ |
| 10 | `/school/guardians` · `school/guardians/page.tsx` | `/school/guardians` | `school.GuardiansView` | `school/guardians/index.html` | D | ⬜ |
| 11 | `/school/cards` · `school/cards/page.tsx` | `/school/cards` | `school.CardsView` | `school/cards/index.html` | D | ⬜ |
| 12 | `/school/devices` · `school/devices/page.tsx` | `/school/devices` | `school.DevicesView` | `school/devices/index.html` | E | ⬜ |
| 13 | `/school/merchants` · `school/merchants/page.tsx` | `/school/merchants` | `school.MerchantsView` | `school/merchants/index.html` | E | ⬜ |
| 14 | `/school/products` · `school/products/page.tsx` | `/school/products` | `school.ProductsView` | `school/products/index.html` | E | ⬜ |
| 15 | `/school/policy` · `school/policy/page.tsx` | `/school/policy` | `school.PolicyView` | `school/policy/index.html` | E | ⬜ |
| 16 | `/school/staff` · `school/staff/page.tsx` | `/school/staff` | `school.StaffView` | `school/staff/index.html` | E | ⬜ |
| 17 | `/school/fees` · `school/fees/page.tsx` | `/school/fees` | `school.FeesView` | `school/fees/index.html` | F | ⬜ |
| 18 | `/school/attendance` · `school/attendance/page.tsx` | `/school/attendance` | `school.AttendanceView` | `school/attendance/index.html` | F | ⬜ |
| 19 | `/school/pooled-funds` · `school/pooled-funds/page.tsx` | `/school/pooled-funds` | `school.PooledFundsView` | `school/pooled-funds/index.html` | F | ⬜ |
| 20 | `/school/disputes` · `school/disputes/page.tsx` | `/school/disputes` (`?open=<id>`) | `school.DisputesView` | `school/disputes/index.html` | F | ⬜ |
| 21 | `/school/p2p-alerts` · `school/p2p-alerts/page.tsx` | `/school/p2p-alerts` | `school.P2PAlertsView` | `school/p2p-alerts/index.html` | F | ⬜ |
| 22 | `/school/privacy` · `school/privacy/page.tsx` | `/school/privacy` | `school.PrivacyView` | `school/privacy/index.html` | F | ⬜ |
| 23 | `/school/tips` · `school/tips/page.tsx` | `/school/tips` | `school.TipsView` | `school/tips/index.html` | F | ⬜ |
| 24 | `/school/payment-issues` · `school/payment-issues/page.tsx` | `/school/payment-issues` | `school.PaymentIssuesView` | `school/payment-issues/index.html` | F | ⬜ |
| 25 | `/platform` · `platform/page.tsx` | `/platform` | `platform.SchoolsView` | `platform/index.html` | G | ⬜ |
| 26 | `/platform/onboard` · `platform/onboard/page.tsx` | `/platform/onboard` | `platform.OnboardView` | `platform/onboard/index.html` | G | ⬜ |
| 27 | `/platform/referrals` · `platform/referrals/page.tsx` | `/platform/referrals` | `platform.ReferralsView` | `platform/referrals/index.html` | G | ⬜ |
| 28 | `/platform/support` · `platform/support/page.tsx` | `/platform/support` (`?school=<id>`) | `platform.SupportView` | `platform/support/index.html` | G | ⬜ |
| 29 | `/platform/payment-issues` · `platform/payment-issues/page.tsx` | `/platform/payment-issues` | `platform.PaymentIssuesView` | `platform/payment-issues/index.html` | G | ⬜ |
| 30 | `/platform/audit-log` · `platform/audit-log/page.tsx` | `/platform/audit-log` | `platform.AuditLogView` | `platform/audit-log/index.html` | G | ⬜ |
| 31 | `/platform/tips` · `platform/tips/page.tsx` | `/platform/tips` | `platform.TipsView` | `platform/tips/index.html` | G | ⬜ |
| 32 | `/student` · `student/page.tsx` | `/student` | `student.PortalView` | `student/index.html` | H | ⬜ |
| 33 | `/give/[token]` · `give/[token]/page.tsx` | `/give/<str:token>` | `give.GiveView` | `give/detail.html` | I | ⬜ |

### Next.js route handlers (not pages) and what replaces them

| Next.js handler | Replacement |
|---|---|
| `POST /api/auth/login` (JSON) | the `/login` form posts to itself (`core.LoginView.post`) |
| `POST /api/auth/logout` | `POST /logout` (`core.LogoutView`, CSRF-protected form in the user menu) |
| `POST /api/auth/locale` | `POST /locale` (`core.LocaleView`): sets the language cookie and the signed-in user's `preferred_language` |
| `/api/proxy/[...path]` (cookie→Bearer proxy) | **removed**: views call services in-process; no browser-side API access |
| `src/proxy.ts` (route protection) | `core.mixins.AreaRequiredMixin` on every page view (same `decideRoute` rules) |

### Action and fragment endpoints (not pages)

Every write the React app made through `/api/proxy/*` becomes a POST to a
URL under the page that owns it (e.g. `POST /school/cards/<id>/freeze`).
`GET` on the same URL returns the confirmation dialog (the old
`ConfirmAction` modal), `POST` performs the action through the service layer
and answers with HTMX events (close dialog, toast, refresh the table) or the
dialog again with the backend's error. Region refreshes (filters, paging,
tabs) are `GET`s to the page URL itself with `HX-Target` naming the region.
The full list is in each area's `urls.py`.

## Component table

| Next.js component | Django replacement (same responsibility) |
|---|---|
| `app/layout.tsx` (root: html, providers, theme) | `web/core/templates/base.html` |
| `components/AppFrame.tsx` (`AppFrame`) | `web/core/templates/core/app_frame.html` (header, sidebar, content regions) + `core.context_processors.app_frame` (school name, logo, brand colour) |
| `AppFrame` → `LanguageSwitcher` | `core/components/language_switcher.html` (`{% language_switcher %}`) |
| `AppFrame` → `NotificationBell` | `core/components/notification_bell.html` + `/notifications/bell` fragment (polls every 60 s with `hx-trigger="every 60s"`) |
| `AppFrame` → `UserMenu` | `core/components/user_menu.html` (`<details>` dropdown with a logout form) |
| `app/school/layout.tsx`, `platform/layout.tsx`, `student/layout.tsx` | `school/layout.html`, `platform/layout.html`, `student/layout.html` (each extends `app_frame.html` with its `NAV`) |
| `Providers.tsx` → `brandShades()` | `core.branding.brand_shades()` (same 10-shade formula) → CSS custom properties |
| `ui.tsx` → `PageHeader` | `core/components/page_header.html` (`{% page_header %}` block) |
| `ui.tsx` → `ErrorAlert` | `core/components/error_alert.html` (`{% error_alert error %}`): the backend's own message + reason code(s) |
| `ui.tsx` → `Money` | `{{ value\|ugx }}` filter (`core.templatetags.web`), same formatting as `formatUGX` |
| `ui.tsx` → `StatusBadge` | `{% status_badge value %}` (same colour map) |
| `ui.tsx` → `Loading` | `core/components/loading.html` (HTMX `hx-indicator`) |
| `ui.tsx` → `DataTable` | `core/components/data_table.html` + `core/components/pagination.html` (`{% pagination page %}`); tables are region partials |
| `ui.tsx` → `ConfirmAction` | `core/components/confirm_action.html` (dialog body: title, description, extra fields, error, Cancel/Confirm) + `core.views.ConfirmActionView` base |
| `ui.tsx` → `Stat` | `core/components/stat.html` (`{% stat %}`) |
| `filters.tsx` → `DateRange`, `DayPicker`, `ChoiceFilter` | `core/components/date_range.html`, `day_picker.html`, `choice_filter.html` |
| `MoneyInput.tsx` | `core/components/money_input.html` (UGX prefix, decimal string, never a float) |
| `StudentPicker.tsx` | `core/components/student_picker.html` + `/school/_picker/students?search=` (server-side search, 300 ms debounce) |
| `SchoolPicker.tsx` | `core/components/school_picker.html` (`<select>` of schools) |
| `StudentForm.tsx` (`StudentFormButton`) | `school/students/_form.html` (create/edit dialog) |
| `cards.tsx` (`IssueCardButton`, `CardActions`, `normalizeUid`) | `school/cards/_issue.html`, `school/cards/_actions.html`; UID validated by `cards.services.normalize_card_uid` |
| `DeviceToken.tsx` (`RegisterButton`, `DeviceTokenModal`, `provisioningPayload`) | `school/devices/_register.html`, `school/devices/_token.html`, `core.qr.provisioning_payload()` + `core.qr.qr_svg()` |
| `pos.tsx` (`Flags`, `TransactionDrawer`) | `{% flags %}` tag, `school/sales/_transaction_drawer.html` |
| `PaymentIssues.tsx` (`DepositIssues`) | `core/components/deposit_issues.html` (+ shared `core.views.deposit_issues_context`) |
| `TipsManager.tsx` (`TipsManager`) | `core/components/tips_manager.html` + `core.tips` view mixin (school & platform) |
| `lib/money.ts` | `core.money` (`to_cents`, `format_ugx`, `compare_money`) |
| `lib/dates.ts` | `core.dates` (`kampala_today`, `shift_day`, `format_datetime`, `format_date`, `hours_since`) |
| `lib/csv.ts` | `core.csv.csv_response()` (server-side CSV, same columns and file names) |
| `lib/roles.ts` | `core.roles` (`home_for`, `decide_route`) |
| `lib/catalogue.ts` (`useCatalogue`) | `core.catalogue.catalogue_names()` |
| `lib/api.ts`, `lib/hooks.ts`, `lib/jwt.ts`, `lib/server/*`, `i18n/request.ts` | not needed (in-process service calls, session auth, Django i18n) |

## Part 4A features not yet built in Next.js

None. Every Part 4A section (A–J) was finished before this migration; all
33 routes above existed. This migration only ports them.

## Part 4A backend changes being kept (all of them)

- `django-cors-headers` + `CORS_ALLOWED_ORIGINS` (default changes in K:
  the dashboard origin `:3000` is no longer needed).
- `core.throttles.AuthThrottle` on `POST /auth/login` and `/auth/register` (`AUTH_THROTTLE_RATE`); the web login reuses it.
- `GET /my-school/`.
- `?status=` on data requests; `?search=`, `?class_name=`, `?card_status=`, `?low_balance=` on students; list filters on cards, wallets, goals, policies, guardians.
- `POST /cards/issue/` and `/reissue/` accept `card_uid` (normalised by `cards.services.normalize_card_uid`); `POST /cards/{id}/reset-pin/`.
- `POST /guardian-verifications/{id}/review/` + `review_notes`, `reviewed_by`, `reviewed_at` (migration `accounts/0002`).
- `GET /users/lookup/`, `GET/POST/PATCH /users/`, `POST /users/{id}/set-password/`.
- Parent `GET /students/{id}/` fix; guardian tenant fix.
- `backoffice` app: `POST /platform/schools/onboard/`, `GET /platform/schools/stats/`, `GET /audit-logs/`, `GET/POST /payments/unmatched-webhooks/…`; `?school=` support filters.
- Student portal: `StudentAccount` (migration `students/0002`), `POST|DELETE /students/{id}/portal-account/`, `GET /student-portal/me/`, the JWT student allowlist.
- `PUBLIC_TOPUP_BASE_URL` pointing at the `/give/{token}` page (default now on the backend origin, `http://localhost:8000/give`).
- Section J: `POST /auth/register`, `GET /parent/dashboard/`, `GET /students/{id}/transactions/`, `GET /students/{id}/spending-controls/`, `GET /payments/payouts/`, `?from_contributor=`; `docs/PARENT_APP_READINESS.md`, `docs/requests/parent/`.
- `seed_demo` additions (platform admin, Jinja admin, pending KYC, Amina's portal login).
- All Part 4A backend tests.

## Places where an exact one-to-one port isn't possible

| React behaviour | Closest Django/HTMX equivalent |
|---|---|
| Mantine `Select` with type-to-search (`StudentPicker`) | text input with `hx-get` (300 ms debounce) listing matches; clicking one fills a hidden `student` field |
| Mantine `MultiSelect` (policy lists) | native `<select multiple>` with a size hint |
| Mantine `TagsInput` (fee classes) | text input, comma-separated (`P4, P5`) |
| Mantine `ColorInput` | native `<input type="color">` |
| Mantine `Stepper` (onboarding) | one form, four step panels shown one at a time by `app.js`, same step labels, same per-step "Next" validation |
| Mantine `SegmentedControl` | radio buttons styled as a segmented control |
| Mantine `notifications.show` toasts | `HX-Trigger: sd-toast` → top-right toast (`app.js`) |
| `CopyButton` | `navigator.clipboard.writeText` (`data-copy` attribute) |
| QR redrawn as the device URL is typed | the URL field `hx-post`s to `/school/devices/qr` (debounced) which returns a fresh SVG; the token travels only in that same-origin POST and is never stored or logged |
| CSV built in the browser | built server-side from the same data, same columns and file names |
| Reconciliation/fees/attendance "fetch all pages then CSV" | the server iterates the full scoped queryset |
| Recharts tooltips formatted with `formatUGX` | Chart.js tooltip callback with the same formatter |
| Daily attendance register computed in the browser | computed in the view from the same two querysets (students of the class, that Kampala day's records) |
| `NEXT_LOCALE` cookie | Django's `django_language` cookie (same behaviour: set at login from `preferred_language`, changed by the switcher) |
| Contributor page calls the public API from the browser so the per-IP throttle sees each contributor | the page is served by Django itself, so `PublicTopUpThrottle` is applied in the view and sees the real client IP directly |

## Sections

- [x] **0. Inventory, plan, DECISIONS entry**
- [x] **A. Shell & auth** — base/app frame templates, CSS/JS/vendor assets, session login/logout (+ throttle, role routing and refusal messages), `/` redirect, language switcher (+ `preferred_language`), notifications bell, branding, scoping helper, WhiteNoise, `build_locale` collects web strings
- [x] **B. Overview, sales, reconciliation (+CSV), review queue**
- [ ] **C. Analytics** (Chart.js)
- [ ] **D. Students (+detail tabs), guardians & KYC, cards**
- [ ] **E. Devices (token once + QR), merchants, products, policy & settings, staff accounts**
- [ ] **F. Fees, attendance, pooled funds, disputes, P2P alerts, data requests, tips, payment issues**
- [ ] **G. Platform back-office**
- [ ] **H. Student portal**
- [ ] **I. Contributor page**
- [ ] **J. Parent-app backend readiness** (verified unchanged; docs updated for the new page origin)
- [ ] **K. Remove the Next.js app** — waiting for the owner's confirmation of the parity table above

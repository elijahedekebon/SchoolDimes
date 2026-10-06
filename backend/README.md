# SchoolDimes Backend

Django 5 + DRF backend for SchoolDimes, a cashless pocket-money and canteen
payments platform for schools. **Part 1**: multi-tenant core, identity/auth,
the append-only ledger, savings goals, i18n scaffolding. **Part 2**:
double-entry money movement (deposits, contributors, gift vouchers,
recurring top-ups, pooled funds, savings, P2P, fees, refunds), spending
policy, canteen POS with offline sync, merchants, attendance,
notifications (en/lg/sw), privacy, and analytics/reconciliation.
See `../docs/PART2_PLAN.md` and `../docs/TESTING_WITHOUT_DEVICES.md`.
See `../docs/API_CONTRACTS.md`, `../docs/DATA_MODEL.md`, and
`../docs/DECISIONS.md` for the full contract, schema, and rationale.

## Stack

Python 3.12, Django 5.1, Django REST Framework, PostgreSQL, Redis,
Celery + Celery Beat (`django-celery-beat`), JWT auth
(`djangorestframework-simplejwt`), Docker Compose for local dev.

## Running with Docker Compose (recommended)

```bash
cp backend/.env.example backend/.env   # already present with dev defaults
docker compose up
```

This brings up Postgres, Redis, the Django API (`:8000`, auto-migrating on
start), a Celery worker, and Celery Beat (idle until Part 2 registers
periodic tasks). Then, in another terminal:

```bash
docker compose exec web python manage.py seed_demo
docker compose exec web python manage.py createsuperuser
```

## Running locally without Docker

```bash
cd backend
python -m venv venv
./venv/Scripts/activate        # Windows; `source venv/bin/activate` on macOS/Linux
pip install -r requirements.txt
# backend/.env points at docker service hostnames (db, redis) -- override
# DATABASE_URL for a bare local run, e.g. a local Postgres or SQLite:
export DATABASE_URL=sqlite:///db.sqlite3
python manage.py migrate
python manage.py seed_demo
python manage.py runserver 0.0.0.0:8000
```

## Tests

```bash
export DATABASE_URL=sqlite:///db.sqlite3   # or a local/test Postgres
pytest
```

The suite is ~380 tests: Parts 1, 2 and 4A (API) plus the web surfaces
(`web/tests/`, Django test client: route parity against seed data, role
protection, tenant isolation on every object URL, CSRF on every POST, the
token-once device flow, card freeze reaching the POS cache, refund and
disbursement limits, onboarding to a first sale, the contributor page end to
end with `mock_webhook`, i18n). In Docker: `docker compose exec web pytest`.
See `docs/TESTING_WITHOUT_DEVICES.md`.
Part 1's original 23 tests cover: tenant isolation (wallets/students visibility across
schools and roles), ledger correctness (cached balance always matches an
independent re-sum of ledger entries, insufficient-funds is rejected
atomically), PIN hashing (never stored/returned raw), guardian↔student
many-to-many correctness (siblings, multiple guardians, no duplicate
links), and school-referral CRUD.

## Demo data (`manage.py seed_demo`)

Idempotent (safe to re-run). Creates:
- Two schools (`Kampala Demo Primary School`, `Jinja Demo Secondary
  School`) linked by a `SchoolReferral`.
- One `school_admin` for the first school.
- Two parents — `parent1` (`GuardianVerification` completed/verified) and
  `parent2` (unverified) — all default passwords are `pw123456`.
- Three students: two siblings sharing `parent1` as guardian, one linked
  to `parent2`.
- Each student gets a card (PIN `1001`/`1002`/`1003`), a main wallet
  seeded via `post_ledger_entry` with a deposit + a POS purchase + a move
  to savings, a savings wallet with one `SavingsGoal`.
- Four financial literacy tips: two in English, one Luganda, one Kiswahili.

## Part 2 apps

| App | What |
|---|---|
| `payments` | aggregator abstraction (mock + skeletons), deposits, payouts, contributor links, gift vouchers, recurring top-ups, webhook |
| `pooled_funds` | transparent group funds |
| `policies` | product categories, products, spending policy (`get_effective_policy`) |
| `wallets` (extended) | system wallets, `post_transfer`, **`authorize_debit`** (the one debit gate), savings ops, P2P + alerts |
| `pos` | devices + device-token auth, offline cache, sync, online purchase, shortfall review |
| `fees`, `attendance`, `merchants`, `disputes`, `privacy`, `analytics` | Sections E–K |
| `notifications` | `notify()`, in-app + stub SMS/push, preferences, push tokens, lg/sw catalogs |

Management commands: `seed_demo`, `simulate_pos`, `mock_webhook`,
`run_recurring_topups`, `build_locale`.

## Web surfaces (Django templates + HTMX)

The school dashboard, platform back-office, student portal and public
contributor page are server-rendered Django templates with HTMX, served by
this same `web` container on `:8000`. There is no separate front-end process
and no Node.js: `docker compose up --build` serves the API and every page.
Code: `web/` (`web.core`, `web.school`, `web.platform`, `web.student`,
`web.give`); route map: `../docs/WEB_MIGRATION_PLAN.md`.

| URL | Who | What |
|---|---|---|
| `/login` | everyone | sign in; parents (mobile app) and canteen/merchant staff (POS app) are refused |
| `/school/...` | `school_admin` | overview, sales, reconciliation, review queue, analytics, students, guardians & KYC, cards, devices, merchants, products, policy, staff, fees, attendance, pooled funds, disputes, P2P alerts, data requests, tips, payment issues |
| `/platform/...` | `platform_admin` | schools, onboarding wizard, referrals, support (`?school=`), payment issues, audit log, platform tips |
| `/student` | `student` (school-issued portal login) | own balances, savings goals, recent purchases, a tip |
| `/give/<token>` | public (no login) | contributor top-up / gift page; the link is the parent app's `share_url` |

Seed accounts (after `manage.py seed_demo`, password `pw123456`):

| Login | Lands on |
|---|---|
| `admin@kampaladps.schooldimes.test` | `/school` (Kampala Demo Primary School) |
| `admin@jinjadss.schooldimes.test` | `/school` (Jinja Demo Secondary School) |
| `platform@schooldimes.test` | `/platform` |
| `student.amina@kampaladps.schooldimes.test` | `/student` |
| `parent1@schooldimes.test` | refused on the web (uses the parent API / app) |

A contributor link to try: `docker compose exec web python manage.py shell -c
"from payments.models import StudentTopUpLink as L; print(L.objects.filter(revoked_at=None).first().token)"`,
then open `http://localhost:8000/give/<token>`. Pay with the page, then
`manage.py mock_webhook <reference shown on the page>`; the page flips to "Paid".

Static files are served by WhiteNoise (`collectstatic` runs at container
start). Web settings in `.env`: `SESSION_COOKIE_SECURE`, `SESSION_COOKIE_AGE`,
`DEVICE_API_BASE_URL` (address in device-provisioning QR codes),
`PUBLIC_TOPUP_BASE_URL`. Translations: `manage.py build_locale` (see
`../docs/TRANSLATIONS_TODO.md`).

## Client apps

The POS app (`../pos-app/`, Flutter) and the parent app (Flutter, Part 4B)
use the REST API under `/api/v1/` with JWT / device tokens. See
`../docs/API_CONTRACTS.md`, `../docs/PARENT_APP_READINESS.md` and
`../docs/DECISIONS.md`.

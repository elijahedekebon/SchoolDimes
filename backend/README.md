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

Part 2 brings the suite to ~165 tests (see `docs/TESTING_WITHOUT_DEVICES.md`).
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

## What's deferred

Payments beyond seed data (deposits, P2P, POS, fee top-ups, pooled funds,
gift vouchers), spending-limit *enforcement*, scheduled recurring top-ups,
attendance, the merchant network, dispute/refund flow, and every client
app (`pos-app/`, `parent-app/`, `admin-dashboard/`) are Part 2–4. See
`docs/DECISIONS.md` for the full breakdown and reasoning.

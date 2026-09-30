# Testing Part 2 without any POS device

The Android POS / merchant / attendance app (Part 3) and the parent app
(Part 4B) don't exist yet. Everything in Part 2 can be exercised from a
terminal and VS Code:

| Tool | What it plays |
|---|---|
| `python manage.py simulate_pos` | the canteen, merchant and attendance devices, over the real device-token API |
| `python manage.py mock_webhook <ref>` | the payment aggregator calling our webhook |
| `python manage.py run_recurring_topups [--now]` | Celery Beat's recurring top-up job |
| `docs/requests/*.http` | the parent app, admin dashboard and devices, one request at a time (VS Code REST Client) |
| `pytest` | everything, automatically (includes an end-to-end `simulate_pos` run) |

---

## 1. Start the stack

### Option A: Docker (matches production)

```bash
cd schooldimes
docker compose up -d --build        # postgres, redis, web (:8000), celery-worker, celery-beat
docker compose logs -f web          # wait for "Starting development server at http://0.0.0.0:8000/"
```
`web` applies migrations on start. Run every command below **inside the web
container**, prefixed with `docker compose exec web`, e.g.
`docker compose exec web python manage.py seed_demo`.

### Option B: no Docker (venv + SQLite, lowest resource use)

```bash
cd schooldimes/backend
python -m venv venv && ./venv/Scripts/activate      # Windows (source venv/bin/activate elsewhere)
pip install -r requirements.txt
export DATABASE_URL=sqlite:///db.sqlite3             # PowerShell: $env:DATABASE_URL="sqlite:///db.sqlite3"
export CACHE_URL=locmemcache://                       # no Redis needed
export CELERY_TASK_ALWAYS_EAGER=True                  # no broker needed; tasks run inline
python manage.py migrate
python manage.py runserver 0.0.0.0:8000              # only needed for REST Client / --base-url
```
(`backend/.env` points at the Docker hostnames `db` and `redis`; real
environment variables override it.)

## 2. Seed the demo data

```bash
python manage.py seed_demo
```
It is safe to re-run. The end of the output looks like this (tokens differ on
every run: device tokens are stored hashed, so the seed **rotates** them and
prints the new ones):
```
Catalogue, school policy and Amina's override (Soda blocked) ready
Part 2 demo data ready (payments, pooled fund, POS sales, dispute, notifications)

Device tokens (rotated on every run; shown once):
  canteen    device #1    Demo canteen till      DEVICE_TOKEN=l0rLKhrFr_09H826Uywgpbi_AyLIVWk0q74Zz4K2uGE
  merchant   device #2    Ntinda Bookshop till   DEVICE_TOKEN=NnhjPpdLI_d4KBgs3tovToSzcK8wvvLmcf4iHcE02JY
  attendance device #3    Main gate              DEVICE_TOKEN=1UcftGDwHNIqWjkZu4rmjjHa0X_WgblE-Dsu358GNtk
Contributor top-up link token:
  TOPUP_LINK_TOKEN=ej5r-7Kh-fFAtxaIHo9le_3LO1PguL1jwoNdKPebGso
Demo seed complete.
```
Logins (password `pw123456` for all): `parent1@schooldimes.test` (Amina and
Brian), `parent2@schooldimes.test` (Cynthia, prefers Luganda),
`admin@kampaladps.schooldimes.test` (school admin),
`canteen@kampaladps.schooldimes.test`, `shop@ntindabookshop.schooldimes.test`.

## 3. Run the POS simulator

```bash
python manage.py simulate_pos                              # Django test client, no server needed
python manage.py simulate_pos --base-url http://localhost:8000   # real HTTP to a running server
```
With `--base-url`, run the command where it shares the server's database
(inside the `web` container for Docker; the same `DATABASE_URL` for a venv).
The simulator still creates devices, freezes a card and tops up wallets
through service functions, but every cache, sync and tap goes over HTTP.

What it does: registers (or reuses) four devices (canteen A, canteen B, a
merchant till, an attendance gate); pulls `/pos/cache/` as each one; freezes
Brian's card *after* the caches were pulled; syncs offline batches; replays
one batch unchanged; posts attendance taps including a duplicate; and prints
the results. Expected output (amounts vary with previous runs):
```
GET /pos/cache/ as canteen_a: 3 cards, 5 products
GET /pos/cache/ as canteen_b: 3 cards, 5 products
GET /pos/cache/ as merchant: 3 cards, 2 products
GET /pos/cache/ as attendance: HTTP 403 (attendance devices can't sell)
Brian's card frozen by a parent AFTER the devices refreshed their caches.
========================================================================
POS SIMULATION SUMMARY
========================================================================
canteen_a: POST /api/v1/pos/sync/ (4 offline sales)
  Amina Nakato   1x Rice & beans                    3000.00 -> applied
  Amina Nakato   1x Soda                            1500.00 -> applied flags=['daily_cap_exceeded', 'item_blocked']
  Brian Nakato   2x Chapati                         1000.00 -> applied flags=['card_frozen']
  Cynthia Auma   3x Rice & beans                    9000.00 -> applied flags=['per_transaction_cap_exceeded', 'daily_cap_exceeded']

canteen_b: POST /api/v1/pos/sync/ (1 offline sales)
  Cynthia Auma   3x Rice & beans                    9000.00 -> shortfall shortfall=4400.00 flags=[..., 'exceeds_offline_ceiling']

merchant: POST /api/v1/pos/sync/ (1 offline sales)
  Amina Nakato   1x Exercise book, 1x Pen           1700.00 -> applied flags=['daily_cap_exceeded']

Replay of canteen_a's batch unchanged: ['duplicate', 'duplicate', 'duplicate', 'duplicate']  (OK: no double effect)
Attendance: 3 records created; statuses ['created', 'created', 'duplicate', 'created']
Final authoritative balances (from the sync responses):
  Cynthia Auma   balance=      0.00  today_spend= 18000.00  card=active
  ...
Totals: 1 applied cleanly, 1 shortfall(s), 5 flagged for review, 0 rejected, 4 duplicates ignored.
```
How to read it:
- **Double spend**: Cynthia's card was sold 70% of its cached balance at two
  tills while offline. The first sync applied in full; the second hit the
  real balance and became a **shortfall**: recorded, never dropped, and sent
  to the review queue.
- **Frozen card** and **blocked item** sales are recorded (they happened) but
  **flagged**.
- The **replay** proves idempotency: same keys, no money moved.
- Now review as the admin: `GET /api/v1/pos/shortfalls/` and resolve one
  (`pos.http`), or look at `GET /api/v1/analytics/reconciliation/`.

## 4. Play the payment aggregator

Payments never credit a wallet until the aggregator's webhook confirms them.
In `AGGREGATOR_MODE=mock` you are the aggregator:
```bash
python manage.py mock_webhook --list                    # pending references
python manage.py mock_webhook SD-DEP-0F7BB00C79B5B0828486
#  POST /api/v1/payments/webhook/ -> HTTP 200 {'status': 'confirmed'}
#  SD-DEP-0F7BB00C79B5B0828486 is now: confirmed
#  Target wallet #3 balance: 13500.00
python manage.py mock_webhook SD-DEP-0F7BB00C79B5B0828486
#  POST /api/v1/payments/webhook/ -> HTTP 200 {'status': 'duplicate'}      (replay: nothing moves)
python manage.py mock_webhook SD-GV-XXXX --fail --reason declined        # a failed gift voucher
```
The command builds the exact signed body a real callback would carry, and
POSTs it to the webhook endpoint (`--base-url` for real HTTP).
The seed leaves one pending USSD top-up for Brian to try this on. New
pending payments come from `payments.http`, `public.http`,
`pooled_funds.http` (contribute), or the parent app later. Mock rules: payer
phones ending in `999` are declined at initiation; payout phones ending in
`998` fail (and the money is reversed).

## 5. Run recurring top-ups now

```bash
python manage.py run_recurring_topups          # only schedules whose next_run_at has passed
python manage.py run_recurring_topups --now    # run each active schedule's next window immediately
#  #1 Brian Nakato      10000.00 weekly   -> confirmed   next run 2026-10-12 05:00 UTC, active=True, failures=0
```
In mock mode the created deposit is confirmed straight away. With Docker,
Celery Beat also runs this every 15 minutes
(`docker compose logs celery-beat celery-worker`).

## 6. Click through every endpoint in VS Code

Install the **REST Client** extension (`humao.rest-client`) and open any
file in `docs/requests/`:
`payments.http, public.http, pooled_funds.http, wallets.http, pos.http,
attendance.http, merchants.http, fees.http, disputes.http,
notifications.http, privacy.http, analytics.http`.
1. Send the two **Log in** requests at the top; their JWTs feed `@parentToken`
   and `@adminToken` automatically.
2. For device requests, paste the `DEVICE_TOKEN`s printed by `seed_demo` into
   `@canteenToken` / `@merchantToken` / `@attendanceToken` (and
   `TOPUP_LINK_TOKEN` into `public.http`).
3. Adjust the id variables (`@studentId`, `@walletId`, …): the GET requests
   in each file show the real ids.
`python docs/requests/_generate.py` regenerates the files.

## 7. Run the tests

```bash
cd backend
pytest -q                     # ~165 tests, SQLite by default (Option B env vars)
# against Postgres (Docker db on localhost:5432):
DATABASE_URL=postgres://schooldimes:schooldimes@localhost:5432/schooldimes pytest -q
```
The concurrency test (two simultaneous debits on one wallet) is only strict
on Postgres, where `select_for_update` really blocks. On SQLite it checks the
weaker "never overspends" property.

## Troubleshooting
- **401 on device calls**: the token rotated. Re-run `seed_demo` or
  `simulate_pos` and paste the new token.
- **403 on `/pos/cache/` with the attendance token**: expected, attendance
  devices can't sell.
- **`Seed data missing`** from `simulate_pos`: run `seed_demo` first.
- **Redis connection errors when running without Docker**: set
  `CACHE_URL=locmemcache://` and `CELERY_TASK_ALWAYS_EAGER=True`.
- **Balances keep dropping across simulator runs**: each run is a new school
  day of sales. The simulator tops wallets back up to at least 8,000 through
  the real deposit path before it starts.

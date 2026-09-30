# Decisions & Assumptions Log

Every judgment call made building SchoolDimes, and why, so later parts (and
later sessions) don't have to re-derive intent from the diff.

## Part 1 — Backend Foundation

### Project location
The proposal's prompt didn't specify where in the filesystem to build this.
The working directory handed to Claude Code was the user's Windows **home
directory** (`C:\Users\SALVATION`), which turned out to already be the root
of a single git repository tracking the *entire user profile* (Documents,
Desktop, AppData, `NTUSER.DAT`, browser caches, etc.) — clearly not
intentional for a software project. Rather than build inside that repo, the
project was created at `C:\Users\SALVATION\Documents\Projects\schooldimes\`
with its own fresh `git init`, keeping it fully isolated from personal files.
This matches how the user's other project folders (`kin-content-manager`,
`sociovate-academy`) sit in the home directory, except each of those has no
`.git` of its own yet — this repo does.

### Toolchain setup performed this session
The machine had no working Python (only the Microsoft Store app-execution
alias stub) and Docker Desktop installed but not running. Installed:
- Python 3.12.10 via `winget install Python.Python.3.12`
- Started Docker Desktop; its engine failed to come up because Docker is
  configured for the **WSL2 backend** (`WslEngineEnabled: true` in
  `settings-store.json`) but WSL2 was not installed on this machine.
  Ran `wsl --install` / `wsl --install --no-distribution` (elevated) to
  enable the "Windows Subsystem for Linux" and "Virtual Machine Platform"
  optional Windows features. **These require a reboot to take effect** —
  the user opted to reboot "when convenient" rather than immediately.
  **Until that reboot happens, `docker-compose up` is unverified on this
  machine.** Everything else (migrations, Django checks, the full pytest
  suite) was verified locally against SQLite via a `venv`, and is expected
  to behave identically against Postgres once Docker is up, since nothing
  in the code depends on SQLite-specific behavior (JSON fields, decimals,
  and constraints used are all supported identically on Postgres).

### Local dev vs. Docker environment split
`backend/.env` (docker-compose's `env_file`) points `DATABASE_URL` /
`REDIS_URL` / `CELERY_BROKER_URL` at the compose service hostnames (`db`,
`redis`), which don't resolve outside the compose network. For local
`venv`-based commands (used to verify this part), `DATABASE_URL` was
overridden to a local SQLite file via a real environment variable, which
`django-environ`'s `Env.read_env()` correctly leaves untouched (it only
`setdefault`s from `.env`, never overrides an already-set real env var).
No code change was needed for this — just noting it so a future session
doesn't "fix" the working `.env` by pointing it at `localhost`.

### Ledger design: guard against negative balances
The proposal doesn't explicitly say what happens on an over-debit, but an
append-only money ledger with no such guard is a real defect, not a
hypothetical one (e.g. a POS purchase racing a P2P transfer out). Added
`core.exceptions.InsufficientFundsError`, raised inside
`post_ledger_entry()` before any row is written, so a failed debit leaves
zero trace and the caller gets a clear exception rather than a silently
negative wallet.

### `Wallet.balance` implementation
Spec says balance must be "computed/cached from ledger entries, never a
directly-written column." Implemented as a real `cached_balance`
`DecimalField`, updated **exclusively** inside
`wallets.services.post_ledger_entry()` (which locks the wallet row via
`select_for_update` inside a transaction), with a separate
`compute_balance()` function that independently re-sums `LedgerEntry` rows
from scratch. Tests assert the two always agree. A plain always-recomputed
property was considered but would not scale once Part 2/3 add
higher-volume POS/P2P traffic, and the spec's own wording ("cached")
implies a stored value is expected.

### Financial literacy tip "translation"
Spec's seed instructions ("two tips in English and one each in Luganda/
Kiswahili") imply translation-by-separate-row, not per-field i18n (e.g.
`django-modeltranslation`, which would need one row with `title_en`,
`title_lg`, `title_sw` columns). Went with separate rows sharing a
`language` field — simpler, matches the seed data shape exactly, and is
consistent with how the client apps will realistically query ("give me the
tip in this user's `preferred_language`").

### `SchoolReferral` reward mechanics
Spec explicitly calls this a placeholder ("the actual discount/billing
mechanics can be a documented placeholder"). `apply_referral_reward()`
only flips `status=applied` and `reward_applied=True` — no billing system
exists yet to integrate with. Future parts/billing work should treat
`reward_applied` flipping `True` as the single event to key off of.

### Card issuance/reissue/freeze permission model
Issuing and reissuing cards is restricted to `school_admin`/`platform_admin`
(an administrative action) — the proposal didn't say explicitly parents
can't issue cards themselves, but nothing in the proposal describes a
self-service card-issuance flow for parents either, and a school
administering its own card stock is the more plausible reading of §4.2/§5.
Freeze/unfreeze, by contrast, is explicitly meant to be usable by parents
("Instant card freeze" is listed as a parent-facing feature in §4.2) as well
as school staff, so `can_manage_card()` in `cards/views.py` is written
generically and reused by both the parent-facing and admin-facing freeze
actions rather than having two separate implementations.

### `GuardianVerification` and `FinancialLiteracyTip` are the two "no direct
`school` FK" exceptions to the multi-tenancy rule
- A parent (and therefore their `GuardianVerification`) isn't reliably
  scoped to one school — siblings could in principle attend different
  schools. Its tenant scoping is derived transitively, through the
  student(s) the parent is linked to via `Guardian`, in
  `GuardianVerificationViewSet.get_queryset()`, rather than via a direct FK.
- `FinancialLiteracyTip.school` is nullable *on purpose*: `null` means a
  platform-wide tip visible to every school. This is the one tenant-scoped
  model where "no tenant" is a valid, first-class state rather than an
  absence of scoping.

### Deferred to Part 2 (explicitly out of scope here)
Deposits (parent MoMo/bank/USSD), real-time low-balance alerts, spending
caps/category restrictions/blocked-item enforcement (only the
`School.policy_defaults` JSON shape exists so far), scheduled recurring
top-ups (Celery Beat is wired into Docker Compose and running, but no
periodic tasks are registered yet), P2P transfers, savings move-in/out
ledger operations, fee top-ups, pooled funds, gift vouchers, dispute/refund
flow, attendance tap-in, and the approved-merchant network.

### Deferred to Part 3 (POS)
The `pos-app/` directory, canteen sale reconciliation, sales analytics
(best-sellers, peak hours, nutrition flags).

### Deferred to Part 4 (parent/admin apps)
`parent-app/` and `admin-dashboard/` directories, the multi-child parent
dashboard UI, offline mode + sync, the parent data/privacy dashboard, and
actual biometric capture/matching (the `Card.biometric_enrolled` boolean
flag exists now; the client-side enrollment/matching flow does not).

## Part 2 — Money movement & operations

### Part 1 conflicts resolved with the product owner (approved before any change)
1. **System wallets extend `Wallet`** rather than a new model: `student` made
   nullable, four system `wallet_type`s added, and DB constraints keep student
   and system wallets apart. There is still exactly one ledger.
2. **`post_ledger_entry(allow_negative=False)`**: a new keyword, honoured only
   for `aggregator_clearing` wallets, plus a `post_transfer()` helper. The
   existing signature and behaviour are unchanged.
3. **Part 1 history was single-sided** (seed deposits and a POS purchase with
   no other side). Migration `wallets.0003_legacy_counter_entries` *appends*
   the missing counter-entries (`reference_id=legacy:<id>`). It is the one
   place that writes ledger rows without calling `post_ledger_entry()`,
   because migrations must use historical models; it replicates the
   function's bookkeeping exactly and is re-runnable. It was verified against
   a copy of the Part 1 dev database: afterwards each school's books sum to
   exactly 0. `seed_demo` now posts balanced transfers.
4. **`Policy` model supersedes `School.policy_defaults`** (Section C). The
   JSON field stays in the schema and the `/schools/` API, but it is no
   longer read.

### Chart of wallets and why the clearing wallet goes negative
Money enters and leaves the platform through the payment aggregator. The
per-school `aggregator_clearing` wallet is the mirror of that outside cash:
confirming a 5,000 deposit debits clearing (−5,000) and credits the
student (+5,000). Its negative balance is "cash the aggregator holds for this
school", and it goes back up as payouts leave. Because every movement is a
transfer, **the sum of all wallets in a school is always 0**. That is a
single, cheap invariant for reconciliation (Section K) and for tests.
A platform-wide clearing wallet was rejected because `LedgerEntry.school` is
non-nullable (Part 1), and per-school clearing keeps every ledger row inside
one tenant. For the same reason, merchant settlement wallets exist per
(merchant, school) pair (Section G).

### One `Deposit` model for all collections
Deposits, gift-voucher payments and pooled-fund contributions are all the
same thing to the aggregator: a collection. One `Deposit` row with a
`purpose` gives a single confirmation service
(`process_payment_event`), a single idempotency constraint, and a single
reference namespace (`SD-DEP-`, `SD-GV-`, `SD-PF-`). The webhook "routes by
reference type" through that one function. `GiftVoucher` and
`PooledFundContribution` hang off their Deposit. Pooled funds and POS
shortfall recovery react to confirmations through the
`payments.signals.deposit_confirmed` signal, so `payments` never imports them.

### Payouts debit first, reverse on failure
A savings withdrawal or external disbursement debits the source wallet into
clearing *before* calling the aggregator, so the money can't be spent twice
while the payout is in flight. If the payout fails (immediately or later by
webhook), a compensating `reversal` transfer returns it. Ledger rows are
never deleted.

### Gift vouchers auto-redeem
As proposed: when the payment is confirmed, the voucher is credited straight
into the student's main wallet (`entry_type=gift_voucher`), marked
`redeemed`, and guardians get a `gift_received` notification that includes
the personal message. Manual redemption would add a step without adding any
protection: the money is already paid, and the voucher can only ever land in
one wallet. `paid` exists as a status but is transitional inside the
confirming transaction. A failed payment marks the voucher `cancelled`.

### Contributor top-up link security model
- The token is 32 random bytes (`secrets.token_urlsafe`, 43 chars), so it
  can't be guessed. It is stored in plaintext so the parent can re-share it
  from the app. It is a low-privilege bearer secret: all it can do is
  *put money in*.
- The public GET returns **only** the student's first name and school name,
  never balances, history, ids or other PII. Deposit responses on the public
  endpoints omit wallet and student ids.
- Unknown, revoked and expired tokens return the same 404, so the link can't
  be used to probe which students exist.
- Revocation is immediate (`active=false`).
- All `/public/` endpoints are throttled per client IP through the Redis
  cache (`PUBLIC_TOPUP_THROTTLE_RATE`, default 20/min).
- Contributors never get an account. One `Contributor` row is created per
  contribution, and public retries are answered before any row is created.

### Webhook edge cases
- A replay is a no-op (`duplicate`), guaranteed by locking the Deposit row
  and checking its status inside the transaction.
- Unknown reference, amount mismatch, or a success after a failure →
  `UnmatchedWebhook`, answered 200 (so the aggregator stops retrying) and
  left for a human. Crediting a mismatched amount, or silently reviving a
  failed payment, would be worse than a short delay.
- A success for an `expired` deposit **is** credited: expiry is our own
  housekeeping timer, and the payer really was charged.

### Idempotency keys
`Deposit.idempotency_key` is globally unique, not per user, because public
contributors have no user. Clients must send UUIDs. A key reused for a
different wallet, amount, purpose or initiator returns 409.

### Recurring top-ups
- They run at `RECURRING_TOPUP_RUN_HOUR` (default 08:00) Africa/Kampala. A
  monthly day is limited to 1–28 so every month has it.
- Double execution is prevented by the database, not by timing: each run
  window's Deposit uses `idempotency_key = recurring:<id>:<scheduled time>`.
  A second Beat fire, a second worker, or `run_recurring_topups` racing Beat
  all hit the unique constraint.
- Missed windows (e.g. Beat down for a week) are **not** back-filled:
  `next_run_at` jumps to the next future slot. Charging a parent several
  times at once after an outage would be a nasty surprise.
- In mock mode the created deposit is confirmed immediately, through the same
  webhook-processing function. With a real aggregator it stays pending until
  the parent approves the prompt.
- After `RECURRING_TOPUP_MAX_FAILURES` (default 3) consecutive failures the
  schedule is paused and the parent is notified. A success resets the
  counter. If the parent is no longer the student's guardian, the schedule
  deactivates itself.

### Mock aggregator conventions
Payer phones ending in `999` are declined at collection; payout phones ending
in `998` fail. Webhooks are HMAC-SHA256 over the raw body. The Flutterwave,
Pesapal and DPO clients are **skeletons only**: they raise
`NotImplementedError` and carry TODOs describing the real calls. No working
integration has been faked.

### Errors: 404 for "not yours"
Objects belonging to another family or another school return 404, not 403,
so ids can't be used to learn what exists elsewhere. 403 is used only when
the caller's *role* can never perform the action.

### URL style
New routes accept both `/x/` (Part 1's style, used in the docs) and `/x`
(the style written in the Part 2 spec), via `core.routers.OptionalSlashRouter`.
Part 1 routes are unchanged.

### Tests use a fast password hasher
Django's default PBKDF2 (870k iterations) is applied to every user password
and card PIN, which made the suite slow. `conftest.py` switches tests to
the MD5 hasher. Production settings are unchanged.

### Local runs without Docker
`CACHE_URL=locmemcache://` replaces Redis for the cache, and
`CELERY_TASK_ALWAYS_EAGER=True` runs tasks inline. SMS/push dispatch
failures never break a money movement: the event stays `pending`, and
`retry_pending_notifications` (Beat) retries it later.

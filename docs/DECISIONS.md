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

### Pooled funds (Section B)
- **Who can do what.** Any parent of the school, or its school_admin, can
  create a fund and contribute. The **creator or a school_admin** can close
  it. **Only a school_admin** (or platform_admin, audit-logged) can disburse.
  Closing is harmless, but disbursing moves shared money, so it needs
  institutional accountability rather than whichever parent created the fund.
- **Totals come from the ledger.** `total_contributed`, `balance` and
  `progress_percent` are recomputed from the fund wallet's ledger entries on
  every read, so the displayed total cannot drift from the ledger.
- **Money left in a closed, undisbursed fund stays in the fund wallet**,
  visible to every parent, until a school_admin disburses it (to the school
  settlement wallet or out to a phone, with a required description). There
  is no automatic refund to contributors: that would need one payout per
  contributor, and some contributions may come from contributors with no
  phone on file. A per-contributor refund flow is a sensible Part 4 admin
  feature.
- A contribution confirmed **after** the fund was closed (the payer approved
  the prompt late) is still credited and logged, because the payer was
  charged. It simply increases what is left to disburse.
- A parent whose children attend several schools must say which school
  (`school`). The value is validated against the schools derived from their
  Guardian links, so it is never trusted blindly.

### Spending controls (Section C)
- **One gate.** `wallets.services.authorize_debit(wallet, amount, context)`
  is called by every debit path *inside* `transaction.atomic()`, and locks
  the wallet row first, so balance **and cap** checks can't race a
  concurrent debit. It returns a `DebitDecision`; `require_debit()` raises
  `DebitRefused` (422). The offline POS sync path calls the same rule engine
  (`debit_violations(..., check_balance=False)`) to *flag* rather than refuse.
- **Parents may only tighten, never loosen.** This is guaranteed twice: by
  resolution (min of caps, union of blocks, intersection of allow-lists,
  AND of `p2p_enabled`), and by a `400 policy_cannot_loosen` so parents get
  a clear error instead of a silently ignored setting. The same resolution
  applies to overrides written by a school_admin, so to loosen for everyone
  the admin changes the school default. (Per-student loosening by an admin
  isn't supported; it can be added later as an explicit flag.)
- **Fee payments are exempt from spending caps** and category rules (a
  3,000 UGX daily snack cap must not stop a 50,000 UGX exam fee). Card freeze
  and balance still apply. Savings moves and withdrawals are exempt too.
- **Freeze blocks every debit, including guardian-initiated ones** (fees,
  savings moves, P2P), as the spec requires. A card presented at a POS is
  checked directly. For non-card debits, any *frozen* card of the student
  blocks, while *lost* cards do not (a lost card is retired and replaced, so
  it shouldn't block the parent from paying a fee). Unfreezing a lost card
  is refused with 409; Part 1 allowed it, which was a latent bug.
- **Low-balance threshold** is an alert level, not a limit, so an override
  simply replaces the school value (it may be higher or lower).
- `School.policy_defaults` is superseded (approved). List-valued keys in it
  (category or item names) could not be migrated because no categories
  existed in Part 1. All seeded schools had `{}`.

### Savings (Section C)
- **Withdrawal window**, interpreting "typically while at home during
  holidays": a guardian sets `withdrawal_window_start/end` on the savings
  wallet. Withdrawals to mobile money are allowed only inside it, and only by
  a guardian (school admins can move money between main and savings but can
  never send it out of the platform). Both fields null = closed (the default).
- A withdrawal debits savings immediately. A failed payout is reversed with a
  compensating `reversal` transfer, and guardians are told the money is back.
- Part 1 named the savings entry types `savings_move_in` / `savings_move_out`
  and its seed used them as *credit side* / *debit side*. That convention is
  kept for both directions, so the type alone doesn't tell you the direction:
  read `direction` and which wallet the entry is on.
- A goal's `reached_at` is stamped once. The notification runs inside the
  posting transaction (so a rolled-back movement never notifies), and SMS/push
  I/O is still deferred to commit by `notify()`.

### P2P transfers (Section C)
- **Who initiates, given students have no login yet.** Two paths, one service
  (`wallets.p2p.p2p_transfer`): (1) a **guardian of the sender** from the
  parent app (`POST /wallets/transfer/`); (2) the **sender at a POS device**
  presenting card + PIN (`POST /pos/p2p-transfer/`, Section D). The recipient
  is chosen by student id or card uid, within the sender's school only. A
  guardian of the *recipient* cannot pull money.
- Both cards must be usable: the sender with an active and not frozen card,
  the recipient with an active card. Both students need P2P enabled.
- **Pattern flagging** (§5 "pressure or bullying"), configurable in settings
  and deliberately simple:
  - `many_distinct_senders`: a student received from ≥
    `P2P_ALERT_DISTINCT_SENDERS` (4) different students within
    `P2P_ALERT_WINDOW_DAYS` (7) — possible extortion or pressure;
  - `repeated_near_cap`: a student sent ≥ `P2P_ALERT_NEAR_CAP_COUNT` (3)
    transfers, each ≥ `P2P_ALERT_NEAR_CAP_RATIO` (80%) of their daily P2P cap,
    in the window — possibly being pressured to pay out daily. It only
    applies when a cap is set.
  One open alert per (student, rule). Admins are notified and review/dismiss
  in `/p2p-alerts/`. Alerts never block transfers; they are for a human.
- P2P history is visible only to the student's guardians and that school's
  school_admin (not canteen/merchant staff).

### Part 1 permission quirk noticed (not changed)
Part 1's `StudentViewSet` applies `IsSameSchoolObject` to detail routes, and
a parent's `school` is null, so **parents get 403 on
`GET /api/v1/students/{id}/`** for their own children (the list works). The
new Part 2 student sub-routes (`p2p-history`, `effective-policy`, …) avoid
this by relying on queryset scoping. Fixing the Part 1 route would change
existing behaviour, so it has been left for the product owner to approve
(a one-line change in `students/views.py`).

### Canteen POS + offline sync (Section D)
- **Shipping PIN hashes to devices is a deliberate offline trade-off.**
  Without it, a card can't be used when the canteen's connection is down,
  which is the normal case the proposal designs for. Mitigations:
  - **Scoping**: a device only ever receives cards of its own school (for
    merchants, the schools that approved them).
  - **Strong hashing**: Django's PBKDF2-SHA256 at 870k iterations with a
    per-card salt. A 4–6 digit PIN is still brute-forceable offline by
    someone who extracts the cache (10k–1M guesses), so hashing alone is
    *not* the protection. It buys time and forces effort per card.
  - **Device revocation** is immediate (token lookup), and **token rotation**
    exists. A lost or stolen till should be revoked from the dashboard at once.
  - **On-device attempt limits** (the app must lock a card after
    `pin_lockout_threshold` wrong PINs) **plus server lockout**: attempts
    reported via sync (or an online wrong PIN) freeze the card on reaching
    the threshold within 24 h, and the freeze reaches every device on its
    next refresh.
  - **Bounded exposure**: offline spend per card is limited by the offline
    spend ceiling, and every offline sale is re-validated and flagged on sync.
  - The Android app (Part 3) must keep the cache in encrypted storage
    (Android Keystore-backed), wipe it on revocation (401), and never log it.
    Recommended future hardening: a separate, lower-value offline PIN
    verifier (e.g. HMAC with a per-device key).
- **Offline spend ceiling** defaults to **2,000 UGX** per school
  (`SchoolSettings.offline_spend_ceiling`), about the price of a snack or
  half a lunch. It caps how far one card can go below its cached balance
  across all offline devices, so the worst-case loss from a double-spend is
  small, and a student whose balance is out of date by one purchase can
  still eat. A shortfall larger than the ceiling is flagged
  `exceeds_offline_ceiling` (a device ignored its ceiling, or the cache was
  very stale).
- **The offline exception to the debit gate.** An offline sale already
  happened at the counter, so sync *records* it even if it now breaks a
  rule: the wallet is debited up to its true balance, and the remainder is a
  `shortfall`. Rule breaches (frozen card, caps, blocked items/categories/
  merchants) become `flags`. Both go to the review queue; nothing is silently
  accepted or dropped. The same rule engine as `authorize_debit` is used
  (`debit_violations`), so offline flags and online refusals always agree.
  Online sales (`/pos/purchase/`) use `authorize_debit()` and are refused
  outright.
- **Wallets never go negative** because of a shortfall. The unpaid remainder
  lives on the PosTransaction (`shortfall_amount − recovered_amount`), not
  as a negative balance, which keeps the Part 1 invariant.
- **Shortfall recovery is not "spending"**, so it bypasses `authorize_debit`
  (a frozen card or a daily cap must not block repaying a debt the school
  approved). It only ever takes what's in the wallet and runs on admin
  decision plus confirmed top-ups.
- **Idempotency is per (device, idempotency_key)** (DB unique constraint), so
  two devices can never collide on each other's UUIDs. Rejected
  transactions are stored too, so replays answer `duplicate` consistently. A
  concurrent replay that loses the insert race is answered `duplicate` from
  the winner's row.
- **Ordering**: within a batch, sales are applied in device timestamp order.
  Across devices, the server applies in arrival order: the second device to
  sync is the one that gets the shortfall. The device timestamp is also the
  "day" for daily-cap flags (clamped to server time).
- **Rejected vs flagged**: only data problems are rejected (unknown or
  out-of-scope card, invalid amount, items not adding up, missing key or
  timestamp). Rule problems are flagged, never rejected, because the food has
  already been handed over.
- **Cache incrementality**: any ledger movement touches the main wallet's
  `updated_at`, so balance changes are picked up via `?since=`. A school-level
  policy or settings change re-sends the whole school rather than computing
  which cards changed. `generated_at` is taken *before* reading, so changes
  that happen during generation are re-sent next time.
- **Heartbeat**: every device request updates `last_seen_at` (throttled to
  once a minute to avoid write amplification); successful syncs update
  `last_sync_at`, and "stale" is measured against that.
- `SchoolSettings` is a new one-row-per-school model rather than new
  columns on `School`, so Part 1's `/schools/` API shape is unchanged.

### Fee top-ups (Section E)
- **Fees are exempt from the daily, weekly and per-transaction snack caps**
  and from category rules. Those limits exist to control pocket-money
  spending at the canteen; a 3,000 UGX daily cap must not make a 50,000 UGX
  exam fee unpayable. Fees still pass through `authorize_debit()`
  (kind `fee_payment`), so a **frozen card** and **insufficient funds** still
  refuse, per the "freeze blocks all debits" rule.
- Who may pay: the student's guardians, and that school's school_admin
  (e.g. paying at the bursar's desk on the parent's instruction). Students
  can't, because they have no login.
- Fees are paid from the **main** wallet only. Savings stay protected; a
  parent can move money out of savings first.
- `applicable_classes` matches `Student.class_name` exactly (e.g. "P4").
  Fixed fees must be paid in full in one payment; range fees allow instalments
  (several payments, each within the range). There's no "amount outstanding
  per student" ledger yet; a fee-balance view is a natural Part 4A
  dashboard feature built on `/fees/payments/`.
- Only completed payments are stored, because a refused payment moved no
  money and there is nothing to audit.

### Attendance tap-in (Section F)
- Attendance uses the same `Device` model and device-token auth as the POS.
  Dedicated `attendance` devices always may record taps; **canteen devices
  may only if the school turns on** `attendance_on_canteen_devices` (off by
  default: a canteen till at lunchtime shouldn't silently become the
  register). Attendance devices can't sell (`403` on `/pos/*`).
- Taps are idempotent per `(device, idempotency_key)`, like POS sales, so an
  offline queue can be resent safely. Duplicates inside one batch are caught
  too.
- Only cards from the device's **own** school are accepted. Attendance is
  never cross-school, even for merchant-approved schools.
- "Today" is the Africa/Kampala day of the tap's device timestamp. The
  first-tap-in guardian notification is **off by default** (per school), to
  avoid a daily notification nobody asked for.
- `in`/`out` is recorded as sent. The server doesn't pair them or infer
  presence; a daily register view is a Part 4A dashboard concern built on
  these rows.

### Approved nearby merchant network (Section G)
- **Two switches.** Each school approves or suspends a merchant for itself
  (`MerchantApproval`), and platform_admin has a platform-wide `status` for
  fraud or abuse. A merchant transacts with a school's cards only while both
  are `approved`. Schools never see or affect each other's approvals.
- **A school_admin who registers a merchant approves it for their own school
  at once.** Other school_admins can see all merchants in order to find and
  approve a shared one, but they only ever see *their own* school in
  `approved_school_ids`, and only their own school's statement lines.
- **Settlement wallet per (merchant, school)**, not one global wallet:
  `LedgerEntry.school` is non-nullable (Part 1), and per-school wallets keep
  every ledger row inside one tenant. Each school can reconcile exactly what
  its students paid the merchant. The merchant's statement aggregates them.
  Paying merchants out to their bank/MoMo is a settlement process for later
  (it would be a `Payout` from the settlement wallet).
- **No parallel payment path**: merchant devices are ordinary `Device`s and
  use the same cache/sync/purchase code. Only the scope (approving schools)
  and the credit wallet differ, both decided in `pos.services`.
- A merchant device is registered by a school_admin of an approving school;
  `Device.school` is that registering school (the owner of the device record),
  while the cards it serves come from every approving school.
- Offline sales from a merchant that has since been suspended arrive with
  cards out of scope and are **rejected** (`unknown_card`), not flagged: once
  a school suspends a merchant, it has withdrawn consent to charge its
  students. Such rows are stored for audit, and the merchant settles directly
  with the school.
- merchant_staff users are linked via `MerchantStaff` rather than a new
  column on Part 1's `User`.

### Disputes & refunds (Section H)
- **Resolvers: that school's school_admin only.** The proposal keeps
  disputes with the school, so platform_admin can *see* disputes but gets
  `403` on resolve. No canteen_staff permission was defined in Part 2: the
  canteen is usually the party being disputed, and letting it adjudicate its
  own sales is a conflict of interest. A delegated "dispute officer"
  permission can be added later if schools ask for it.
- **The refund comes from whoever received the money**: the school's
  settlement wallet for canteen sales and fees, and the merchant's
  settlement wallet for that school for merchant sales. It always goes to
  the student's **main** wallet.
- **Refund cap**: across all disputes on one transaction, refunds never exceed
  what was actually debited (`applied_amount + recovered_amount` for POS
  sales, so an un-recovered shortfall can't be "refunded"). The disputed row
  is locked during resolution so two admins can't both pass the check.
- **One open dispute per transaction** is a DB constraint. After resolution a
  new dispute may be raised (e.g. a denied dispute with new evidence), still
  under the cap.
- **Disputable**: POS/merchant sales (via `pos_transaction`), fee payments
  and shortfall recoveries (via `ledger_entry`). **Not disputable**: P2P (a
  refund would have to come out of another child's wallet, so that's a
  pastoral conversation plus a reverse transfer, not a refund), deposits
  (those go through the aggregator's chargeback process), and rejected sales
  (no money moved).

### Notifications (Section I)
- **Rendered once, at creation, in the recipient's language.** The stored
  title/body are what the user saw. The machine-readable `payload` lets
  clients re-render or act (e.g. one-tap top-up) without parsing text.
  Reason/status/rule codes in payloads are translated through
  `notifications/labels.py`.
- **Translations without GNU gettext.** The dev machine has no `msgfmt`, and
  the Docker image doesn't need one: `manage.py build_locale` generates the
  `.po` files and compiles the `.mo` files in pure Python from
  `notifications/translations.py`, and both are committed. Kiswahili is
  standard East African usage. **Luganda is best-effort and must be reviewed
  by a native speaker before launch**; every string is in one file to make
  that review easy. Untranslated strings fall back to English.
- **Channels**: in-app is authoritative and always on by default. SMS
  (Africa's Talking) and push (FCM) are clearly stubbed backends that log
  what they would send and mark the event `logged`, never `sent`. Where
  credentials plug in is documented in `notifications/backends.py` and
  `.env.example` (`SMS_BACKEND`, `AFRICASTALKING_*`, `PUSH_BACKEND`, `FCM_*`).
  No working integration has been faked.
- **Dispatch never breaks money movement**: SMS/push are enqueued with
  `transaction.on_commit`, so a rolled-back transfer never notifies. If the
  broker is down, the event stays `pending` and
  `retry_pending_notifications` (Beat, every 10 min) retries it.
- **Low balance** is evaluated on the ledger signal (crossing from ≥ to <
  the threshold on a main-wallet debit, so it can't repeat while the balance
  stays low) and throttled per guardian per wallet in the Redis cache
  (`LOW_BALANCE_ALERT_THROTTLE_HOURS`, default 12). If the surrounding
  transaction rolls back after the cache key was set, one alert may be
  suppressed for the throttle window; that's an acceptable trade-off for a
  reminder.
- Card freeze/unfreeze/lost notify the **other** guardians: the actor
  already knows.

### Privacy (Section J)
- **Deletion = redaction, never ledger deletion.** The ledger is the audit
  trail; deleting it would break every balance, the double-entry invariant,
  and the school's legal records. A completed deletion request strips
  personal data (names, contact details, date of birth, photo, KYC ID
  number), deactivates access (unusable password, cards `lost`, schedules and
  links stopped), and leaves financial rows pointing at a redacted
  placeholder. This is stated to the parent in `retention_notice` (on the
  request, and appended to the handler's notes) so there's no surprise.
- **A child's data can't be deleted while their wallets hold money.** That
  money belongs to the family; the admin gets `409 balance_not_zero` until it
  has been withdrawn or spent.
- On a parent's own deletion, children who have **another guardian** are
  left intact (that guardian still has a relationship with the school), and
  only children for whom they were the **sole** guardian are redacted.
- Handled by the school's school_admin (the data controller for its students)
  and audit-logged for everyone (`force=True`), not only platform_admin.
- `my-data` is parent-only in Part 2 (students have no login). It includes
  the parent's own KYC details: it's their own data, and GDPR-style access
  rights cover it.

### Analytics & reconciliation (Section K)
- **No duplicated storage.** Every figure is an aggregate query over the
  source rows at request time. At pilot-school volumes (hundreds of sales a
  day) this is fast. Redis caching of aggregates was allowed by the spec but
  not added yet, because stale analytics would be worse than slightly slower
  ones. The natural place to add it is a short-TTL cache in
  `analytics/views.py`, keyed by (endpoint, school, range).
- **Sales are bucketed by the device timestamp** (when the student actually
  bought), while **reconciliation is by sync day** (when the ledger moved),
  because reconciliation must line up with ledger rows. Both are documented
  in the API.
- **gross vs collected**: offline shortfalls make them differ, and both
  matter (what the canteen handed over vs what it has been paid).
- **Tenant scoping**: school_admins only ever see their own school.
  platform_admin sees cross-school **summaries** (sales, best-sellers, peak
  hours, categories, reconciliation), but **never per-student spending**,
  which stays with the student's guardians and school.
- **Nutrition flag**: share of item revenue in categories the school flags
  `is_unhealthy`. Deliberately simple; per-item nutrition data is out of scope.

### Seed data (Section L)
`seed_demo` keeps everything Part 1 seeded and adds (in
`core/management/commands/_seed_part2.py`):
- users `canteen@kampaladps.schooldimes.test` (canteen_staff) and
  `shop@ntindabookshop.schooldimes.test` (merchant_staff), password `pw123456`;
- categories Meals / Snacks / Sugary drinks (**unhealthy**) / Stationery;
  canteen products Rice & beans 3,000, Chapati 500, Mandazi 300, Soda 1,500,
  Juice 1,000; merchant products Exercise book 1,200 and Pen 500;
- school policy: daily 6,000, per purchase 5,000, P2P 3,000/day, low
  balance 2,000; **Amina's override: daily 4,000 and Soda blocked**;
- merchant "Ntinda Bookshop", approved for the Kampala school, with its staff user;
- three devices (canteen, merchant, attendance);
- fee categories Exam fee (6,000, P4/P6), School trip (1,000–20,000), Uniform (25,000);
- a confirmed 15,000 top-up for Amina, a **pending** 5,000 USSD top-up for
  Brian (for trying `mock_webhook`), a 5,000 gift voucher from contributor
  "Jjajja Nalongo" with a message, a pooled fund "P4 trip to Entebbe Zoo"
  (target 60,000) with two confirmed contributions (17,500), a weekly
  recurring top-up for Brian, and a contributor link for Amina;
- four POS sales with line items from yesterday, one open dispute, and the
  notifications all of the above produced.

**Re-runnable**: every money movement uses a fixed idempotency key and goes
through the real services, so a second run moves nothing (tested). Device
tokens are stored hashed and can't be shown again, so **each run rotates the
three demo devices' tokens and prints the new ones**, together with the top-up
link token. In non-mock aggregator mode, confirmation-dependent data
(deposits, voucher, pooled contributions) is skipped.

### Bug found while seeding
`students.access.user_school_ids()` used `values_list().distinct()` on
`Student`, whose `Meta.ordering` includes `name`. Django adds ordering
columns to `SELECT DISTINCT`, so a parent with two children in one school got
that school twice (and was asked to "choose a school" for a pooled fund).
Fixed with `.order_by()`; there's a regression test.

### Testing without devices (Section M)
- `simulate_pos` exercises the **exact device contract** (device-token auth,
  `/pos/cache/`, `/pos/sync/`, `/attendance/tap/`) through Django's test client
  by default (no server needed, same routing, auth and serializers), or over
  real HTTP with `--base-url`. Setup steps that a *person* would do (register
  devices, freeze a card, top up wallets) call the same service functions
  the endpoints use, as the spec asks.
- Each run gets fresh idempotency keys and rotated device tokens, and first
  tops up the three demo students through the real deposit path, so it can be
  run repeatedly. It's covered by a CI-style test
  (`pos/test_simulator.py`), along with `mock_webhook` and
  `run_recurring_topups`.
- `run_recurring_topups --now` runs each active schedule's **next** window
  immediately (and advances it), so running it twice moves two windows.
  Without `--now` it only runs what's due, which is idempotent.
- `docs/requests/*.http` is generated by `docs/requests/_generate.py`, and a
  check resolves every request path against Django's URL config (143 requests,
  all routed).

### Daily caps count the day the student bought (found by the simulator)
Spend toward daily/weekly caps (and the cache's `today_spend`) is the gross
amount of recorded POS sales whose **device timestamp** falls in the
Kampala day/week (`policies.services.purchases_between`). The first
version summed ledger entries by *sync* time, which charged a sale made
yesterday offline and synced this morning against today's cap.

### Found only on PostgreSQL: row locks across a nullable join
`Wallet.objects.select_for_update().select_related("student")` becomes a
`LEFT JOIN` now that `Wallet.student` is nullable (system wallets), and
PostgreSQL refuses `FOR UPDATE` on the nullable side of an outer join.
SQLite ignores `FOR UPDATE`, so the SQLite suite passed while 40 tests
failed on Postgres. Every such lock now uses `select_for_update(of=("self",))`,
which locks only the row that is actually being protected. **Lesson for
later parts: run the suite on Postgres (the Docker `db` service) before
calling anything done.**

### docker-compose: celery-beat waits for migrations
With `docker compose up` from scratch, `celery-beat` started before `web` had
run `migrate`, and crashed on the missing `django_celery_beat` tables (Part
1 never verified the compose stack, because Docker wasn't running then). Its
command now loops on `manage.py migrate --check` before starting beat. No
service was added. Verified: all five services come up, Beat installs the
Part 2 schedule, and the worker runs `payments.tasks.run_recurring_topups`
and `notifications.tasks.retry_pending_notifications`.

### Verification performed for Part 2
- Full suite green on **SQLite** and on **PostgreSQL 16** (the Docker `db`
  service), including the strict concurrency test (one debit waits on the row
  lock, then gets `insufficient_funds`).
- A copy of the Part 1 dev database was migrated forward: all Part 2
  migrations apply, the legacy counter-entry migration balances the books to
  exactly 0, `seed_demo` runs twice without moving money the second time, and
  no wallet's cached balance drifts from its ledger re-sum.
- `docker compose up -d --build` brings up exactly the Part 1 services;
  inside `web`: `seed_demo`, then `simulate_pos --base-url http://localhost:8000`
  (real HTTP to the running server), then `mock_webhook <ref> --base-url …` and
  `run_recurring_topups --now`, all against Postgres, leaving each school's
  books at exactly 0.

### What Part 2 leaves for later parts
- **Part 3 (Android POS/merchant/attendance app)**: everything server-side
  is ready. See the handover notes in the Part 2 summary and the Section D
  API contract (cache format, exact PIN scheme, sync semantics, what to
  enforce offline).
- **Part 4A (admin dashboard)**: review queues exist as APIs (POS
  shortfalls/flags, disputes, P2P alerts, data requests, unmatched webhooks
  are in Django admin only), plus analytics and reconciliation.
- **Part 4B (parent app)**: deposits (poll `GET /payments/deposits/{id}/`),
  notifications with one-tap top-up payload, push-token registration, policy
  overrides, savings, P2P, disputes, privacy export.
- **Real integrations (any time)**: aggregator clients (Flutterwave /
  Pesapal / DPO skeletons), Africa's Talking SMS, FCM push.
- **Native-speaker review of Luganda strings** (`notifications/translations.py`).

## Part 4A — Web surfaces & parent-app readiness

### Dashboard stack
- **One Next.js app** (`admin-dashboard/`, App Router, TypeScript, Next 16)
  serves the school admin area (`/school`), the platform back-office
  (`/platform`), the student portal (`/student`) and the public contributor
  page (`/give/{token}`). A separate `platform-backoffice/` app wasn't needed:
  the back-office is ~7 pages that share the shell, API client and auth.
- **Mantine** is the single component library (tables, forms, modals,
  notifications, dates). **Recharts** is the single charting library.
  **next-intl** handles en/lg/sw. **qrcode.react** draws the device-token QR.
  **Vitest** for unit tests, **Playwright** for end-to-end.
- Next.js 16 renamed middleware to `proxy` (`src/proxy.ts`); it does the
  optimistic role check. Every API call is still authorised by Django.

### Tokens live in httpOnly cookies behind a server-side proxy
The browser never sees a JWT. `POST /api/auth/login` (a Next.js route handler)
logs in against Django and stores `access`/`refresh` in `httpOnly`,
`SameSite=Lax` cookies (`Secure` when `COOKIE_SECURE=true`). The page calls
`/api/proxy/<path>` on its own origin; the handler forwards to
`<API>/api/v1/<path>` with `Authorization: Bearer`, refreshes once when the
access token is expired or Django answers 401 (rotating both cookies), and
clears the cookies when the refresh fails (the page then shows "session
ended"). Concurrent requests share one refresh call, because refresh tokens
rotate and are blacklisted on use. Why not localStorage: any XSS could read a
token there; an httpOnly cookie can't be read by script. CSRF: the proxy
only accepts same-origin `fetch` with JSON bodies and `SameSite=Lax` cookies
are not sent on cross-site POSTs. Logout calls Django's `/auth/logout`
(blacklists the refresh token) and clears the cookies.

### Who can use the web dashboard
`school_admin` → `/school`, `platform_admin` → `/platform`, `student` →
`/student`. Parents (mobile app) and canteen/merchant staff (POS app) are
refused at login with a clear message, and their freshly issued refresh
token is blacklisted at once. A platform_admin is sent to `/platform` rather
than into a single school's admin pages: cross-tenant reads live under
`/platform/support`, where every request names the school explicitly
(`?school=`), and the backend audit-logs platform_admin writes.

### Language
The UI locale is a cookie (`NEXT_LOCALE`), set at login from the JWT's
`preferred_language` claim. The switcher updates the cookie and PATCHes
`/me {preferred_language}`. The proxy forwards it as `Accept-Language`, so
Django's error `detail`s come back translated too. lg/sw message files only
contain keys a native speaker has provided; everything else falls back to
English and is listed in `docs/TRANSLATIONS_TODO.md`.

### Money and time in the browser
Amounts stay decimal strings end to end. The dashboard parses them to integer
cents (`BigInt`) only to compare or sum, and formats with string grouping;
no `parseFloat` on money. Day pickers and "today" use Africa/Kampala.

### Backend additions in Section A
- `django-cors-headers`, origins from `CORS_ALLOWED_ORIGINS`.
- `core.throttles.AuthThrottle` on login (`AUTH_THROTTLE_RATE`, 10/min/IP):
  the dashboard and parent app expose a password form to the internet.
- `GET /my-school/`: staff couldn't read their own school's name/branding
  (`/schools/` is platform-only and also exposes policy JSON).

### Section B — overview, sales, reconciliation, review queue
- The overview is composed client-side from existing endpoints (sales
  summary, reconciliation, and `page_size=1` counts of the review queue, open
  disputes/P2P alerts, stale devices and pending data requests) rather than a
  new aggregate endpoint: every number then links to the page that explains it.
  The only backend change is a `?status=` filter on data requests.
- Reconciliation CSV is generated in the browser from the reconciliation
  response, so the exported figures are exactly the ones on screen.
- Charts convert decimal strings to whole shillings only for bar heights;
  every amount shown as text is the API's string.

### Section C — analytics
Charts and tables come straight from the four Part 2 analytics endpoints; the
page invents no numbers. What Part 2 documented as simplified is labelled on
screen: the nutrition flag only counts sales that were sent **with line items**
(item-less sales can't be categorised). Per-student spending is picked through
a server-side student search (`/students/?search=`, added here) so it scales
past one page of students.

### Section D — students, guardians, cards
- **Card UID format.** NFC readers report a tag's UID as bytes; tools print
  them as `04:A2:2B:…`, `04A22B…` or reversed. We store lowercase hex in the
  reader's byte order with no separators, the same form Android's
  `Tag.getId()` gives when hex-encoded. The server normalises admin input;
  device endpoints match exactly, so Part 3 must normalise before sending.
  Changing sync to normalise as well was considered and rejected: it would
  change Part 2 behaviour and hide device bugs.
- **PIN reset** is admin-only, never shows a hash, and doesn't unfreeze a card
  locked after wrong PINs. Unfreezing stays a separate, deliberate action.
- **KYC review** didn't actually work before: `status` was read-only in the
  serializer, so an admin `PATCH` silently did nothing. Added a dedicated
  `review` action with notes and an audit trail instead of changing PATCH.
- **Linking guardians** uses exact-email lookup of an existing parent account
  (parents self-register in the app). Partial search was rejected: it would
  let any school admin enumerate every parent on the platform.
- **Fixed: parents got 403 on their own child's `GET /students/{id}/`.** This
  was the Part 1 quirk Part 2 left for approval; the product owner asked us
  to fix everything outstanding. Reads now rely on queryset scoping, as every
  Part 2 route does.
- **Tenant gap closed:** Part 1 let a school_admin create a `Guardian` row for
  another school's student. Now `404`.
- `?low_balance=true` compares to the school default threshold, not each
  student's override. It is a triage filter; the exact per-guardian rule
  stays in notifications.
- The dashboard generates a 10-shade palette from the school's
  `primary_color`. With identical shades, Mantine's light variants rendered
  text in the background colour.

### Section E — devices, merchants, products, policy, staff
- **Device token shown once** in a modal that can't be dismissed by clicking
  outside, with a copy button and a QR code. The QR holds JSON with
  `type`/`v` so the POS app can reject unrelated codes and the format can
  evolve. It also includes the backend address, because a phone on the
  school Wi-Fi can't use `localhost`.
- **Staff accounts** (`/users/`) were missing: without them a school couldn't
  give canteen or merchant staff a login, or add a second admin, without
  engineering help. Merchant staff are created and linked to the merchant in
  one transaction; the existing `link_staff()` rule (merchant approved for
  your school) is reused. The account is rolled back if the link is refused.
- The policy page edits the school default through the existing
  `PATCH /policies/{id}/` and `PATCH /school-settings/`. Overrides show who
  set them (`updated_by_role`), so admins can see which limits came from
  parents.

### Section F — fees, attendance, pooled funds, disputes, P2P alerts, privacy, tips, payment issues
No backend changes: every page uses the Part 2 endpoints as documented.
- **Daily attendance register** is built in the browser from
  `/students/?class_name=` plus `/attendance/?date=` (all pages). Present = at
  least one `in` tap that Kampala day. A server-side register endpoint isn't
  needed at current school sizes; revisit if classes grow past a few hundred.
- **Refund limits are shown and enforced in the UI** (remaining =
  `original_amount − refunded_total`, in integer cents), but the backend's
  locked check (`422 refund_exceeds_original`) remains the authority.
- **Deletion requests** show the retention notice before an admin completes
  one, because completing is irreversible.
- **Payment issues** for a school are failed, expired or still-pending
  collections (`/payments/deposits/?status=`). Unknown webhook references
  aren't tied to a school, so they live in the platform back-office (Section G).
- Fee payments, pooled-fund disbursements and other money-moving forms carry
  a client-generated idempotency key that's only renewed after success, so a
  double click or retry can't pay twice.

### Section G — platform back-office
- **One onboarding endpoint, one transaction.** Creating a school used to
  mean four separate calls (school, settings, policy, admin) plus lazily
  created system wallets, and a half-finished school was possible.
  `POST /platform/schools/onboard/` does it all atomically, so a platform
  admin can onboard a school without engineering. A test proves that a school
  created only this way can log in its admin, add a student, issue a card,
  register a device, take a mock-confirmed top-up and complete a POS sale.
- The back-office reuses `/schools/`, `/school-referrals/` and the
  `?school=`-scoped support reads rather than duplicating them under
  `/platform/`. Only things that had no endpoint were added.
- **Unknown webhook references** have no school, so they are reviewed only in
  the platform back-office. Marking one reviewed moves no money; fixing a
  payment stays a deliberate reconciliation with the aggregator.
- `seed_demo` now also creates `platform@schooldimes.test` and
  `admin@jinjadss.schooldimes.test` (password `pw123456`), plus a pending KYC
  submission for parent2.
- The Playwright onboarding test creates a new "E2E School <timestamp>" in
  the dev database on every run; that's intentional (it's the real flow).

### Section H — student portal: school-issued login, not card + PIN
- **Chosen: a school-issued `student` login** (email + password set by the
  school admin), created per student from the student page. **Rejected: card
  UID + PIN on the web.** A card PIN is 4–6 digits, so a public web form
  keyed by a card UID could be brute-forced by anyone who has read the UID.
  Counting web failures towards the existing PIN lockout would also let
  anyone freeze any child's card from the internet. Passwords are longer,
  login is rate-limited (`AUTH_THROTTLE_RATE`), and the login can be removed
  without touching the card.
- **Defence in depth.** Many Part 1/2 querysets scope "any non-parent role"
  to the user's school, because they were written for staff. A student login
  would therefore have seen every student's wallets and cards. Instead of
  patching each queryset, the default JWT authentication class only lets
  `student` logins reach an allowlist (`/me`, `/my-school/`,
  `/student-portal/me/`, tips, refresh/logout). A test walks the main
  school endpoints and expects `403` for each.
- The portal is read-only and simple: balances, savings goals, the last 10
  purchases with items, and one tip in the student's language. The physical
  card remains the primary student client.

### Section I — contributor page security model (confirms Part 2's)
- The link token (43-char URL-safe random, revocable, optional expiry) is the
  only credential. The page shows **only** what the public endpoint returns:
  the student's first name and the school's name. Unknown, revoked and
  expired tokens all look the same ("this link isn't active").
- **Throttling stays in the backend** (`PUBLIC_TOPUP_THROTTLE_RATE`, per IP).
  So the throttle counts real client IPs, this page calls the API from the
  browser rather than through the dashboard's server proxy (through the
  proxy, every contributor would share the dashboard server's IP). Trusting
  `X-Forwarded-For` was rejected: it would let any direct caller spoof IPs.
- **Cheap bot deterrent:** a hidden honeypot field and a 3-second minimum
  fill time. No CAPTCHA (an extra third party, and heavy on low-end phones).
- **Idempotency:** one key per attempt, kept on a network-error retry and
  renewed only after success. A flaky connection can't create two
  collections.
- Status is polled every 3 s for up to ~3 minutes; after that the page says
  it's safe to close (money is only credited on the aggregator's
  confirmation).

### Section J — parent-app readiness
- **Registration is parent-only.** `POST /auth/register` ignores any `role`;
  staff accounts come from admins (`/users/`) and student logins from the
  school. Throttled like login; Django's password validators apply.
- **One dashboard call** (`/parent/dashboard/`): the home screen previously
  needed per child 6+ calls (wallets, goals, cards, policy, history,
  notifications). On slow mobile data that's the difference between a usable
  and an unusable app. A fixed number of queries per child; recent history
  is capped at 5.
- **History rows carry their dispute target.** The app sends a row's
  `dispute_target` straight to `POST /disputes/`, so it never has to know
  which entry types are disputed by POS transaction vs ledger entry.
  `open_dispute` prevents a second dispute on the same sale in the UI (the
  DB constraint remains the authority).
- **Spending controls** returns the school default next to the override, so
  the app can show "school limit: 5,000 · your limit: 3,000" and grey out
  loosening. The backend still rejects loosening (`policy_cannot_loosen`).
- **KYC-lite** is shown but not enforced: nothing in Parts 1–2 restricts an
  unverified parent, and inventing restrictions in the app was ruled out.
- `docs/PARENT_APP_READINESS.md` maps every 4B screen to its endpoints;
  `docs/requests/parent/` has a runnable file per area.

### Part 4A — local testing note
`backend/.env` (not committed) sets `AUTH_THROTTLE_RATE=100/min` on the dev
machine because the Playwright suite signs in many times a minute. The
default stays `10/min`.

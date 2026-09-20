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

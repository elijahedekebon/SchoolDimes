# Part 2 Plan

Working checklist for Part 2 (money movement + operations). If a session is
interrupted: re-read this file and `git log`, then continue from the first
unticked section. Each section ends with: tests green → tick here → docs
updated → commit `Part 2 – Section X: ...`.

## Part 1 conventions observed (and followed)

| Concern | Part 1 convention |
|---|---|
| Amounts | `DecimalField(max_digits=12, decimal_places=2)`, UGX implied, no currency column |
| Moving money | `wallets.services.post_ledger_entry(*, wallet, amount, direction, entry_type, reference_id="", description="") -> LedgerEntry`; `@transaction.atomic`, `select_for_update` on the wallet, raises `core.exceptions.InsufficientFundsError` before writing on over-debit; updates `Wallet.cached_balance` |
| Balance truth | `compute_balance(wallet)` re-sums entries; tests assert `cached_balance == compute_balance()` |
| Tenant scoping | Derived from `request.user.school_id`, or for parents from `Guardian` links; `platform_admin` sees all. Helpers in `core/permissions.py` (`is_platform_admin`, `is_school_admin`, `is_parent`, `IsSameSchoolObject`, …) and per-app `*_visible_to(user)` queryset functions |
| Views | DRF `ModelViewSet`/`GenericViewSet` + `@action`, registered on `DefaultRouter` → **trailing slash** (`/api/v1/cards/{id}/freeze/`). Auth paths are the exception (`/auth/login`, `/me`, no slash) |
| Services | `<app>/services.py` plain functions (`issue_card`, `freeze_card`, `mark_guardian_verification`, …) |
| Tests | pytest-django, one `tests.py` per app, shared fixtures in `backend/conftest.py` (`school_a/_b`, `school_admin_a/_b`, `parent_user`, `student_a1/_a2/_b1`, `main_wallet_a1`, `card_a1`, …); run on SQLite locally |
| PIN hashing | `django.contrib.auth.hashers.make_password` (Django 5.1 default: `pbkdf2_sha256`, 870 000 iterations, random salt) |
| Docs | `API_CONTRACTS.md` (per app, `#### METHOD path`, roles, body, response), `DATA_MODEL.md` (per app field tables), `DECISIONS.md` (`### heading` + rationale) |
| i18n | `LANGUAGES` en/lg/sw, `LOCALE_PATHS=[backend/locale]` — **no locale files exist yet** |

## Conflicts with Part 1 — all four APPROVED by the product owner (recommended option each time)

1. **System wallets don't fit `Wallet`.** `Wallet.student` is required and
   `wallet_type` is only `main|savings`, so there is nowhere to put a school
   settlement / aggregator clearing / pooled-fund / merchant settlement
   wallet. Proposed: make `Wallet.student` nullable, add wallet types
   `school_settlement`, `aggregator_clearing`, `pooled_fund`,
   `merchant_settlement`, add a nullable `merchant` FK, plus DB check
   constraints (student wallets must have a student, system wallets must not).
   Additive only — no existing row changes.
2. **`post_ledger_entry()` forbids negative balances on every wallet.** The
   aggregator clearing wallet is a receivable and must go negative when a
   deposit is confirmed (debit clearing / credit student). Proposed: new
   keyword `allow_negative=False`, honoured **only** for
   `aggregator_clearing` wallets (enforced inside the function). Plus a new
   `post_transfer()` helper that calls `post_ledger_entry()` twice inside one
   atomic block. Existing signature and behaviour unchanged.
3. **Part 1's ledger history is single-sided.** `seed_demo` posted deposits
   and a POS purchase with no counter-entry, so "system wallets balance
   overall" can't hold for existing data. Proposed: a data migration that
   *appends* balancing counter-entries (aggregator clearing for legacy
   deposits, school settlement for legacy POS purchases); nothing is deleted
   or edited. `seed_demo` switches to balanced service calls for new data.
4. **Policy already half-exists as `School.policy_defaults` (JSON).** Spec
   wants a `Policy` model with FKs to products/categories/merchants.
   Proposed: new `Policy` model (school default row + per-student override
   rows); a data migration copies any recognised keys out of
   `policy_defaults`; the JSON field is left in place (not removed, API
   unchanged) but documented as superseded and no longer read.
5. **URL trailing slashes.** The Part 2 spec writes paths without a trailing
   slash; Part 1 routers use one. Decision (no approval needed, nothing
   existing changes): new routers accept both, docs show Part 1's
   trailing-slash form.
6. **Card freeze/unfreeze endpoints already exist.** Extended in place
   (notifications, lockout reason) — same paths, same response shape.

## Sections

### [x] A. Payments — deposits, contributors, gift vouchers, recurring top-ups
- Models: `Deposit`, `Contributor`, `StudentTopUpLink`, `GiftVoucher`, `RecurringTopUp`, `UnmatchedWebhook`
- `payments/aggregator_client.py`: interface, `MockAggregatorClient`, skeleton `FlutterwaveClient`/`PesapalClient`/`DPOClient`
- Services: `initiate_deposit`, `confirm_payment` (single confirmation path for deposit / gift voucher / pooled-fund contribution), `fail_payment`, `create_topup_link`, `revoke_topup_link`, `run_due_recurring_topups`
- Endpoints: `payments/deposits/` (POST, GET list, GET detail), `payments/topup-links/` (POST, GET, POST revoke), `public/topup-links/{token}/` (GET), `public/topup-links/{token}/deposits/`, `public/topup-links/{token}/gift-vouchers/`, `payments/gift-vouchers/`, `payments/webhook/`, `payments/recurring-topups/` CRUD
- Celery beat: `payments.tasks.run_recurring_topups` (every 15 min), expire stale pending deposits
- Env: `AGGREGATOR_MODE`, `PAYMENT_AGGREGATOR_API_KEY`, `PAYMENT_AGGREGATOR_BASE_URL`, `PAYMENT_AGGREGATOR_WEBHOOK_SECRET`, `RECURRING_TOPUP_MAX_FAILURES`, `MAX_TRANSACTION_AMOUNT`
- Tests: credit only on confirmed webhook, replay no-op, bad signature, failed = no money, link exposes no balance, revocation, throttling, gift voucher credit + notification, recurring schedule with frozen clock / double fire / auto-pause
- Also: chart of system wallets + `post_transfer` + `authorize_debit` skeleton (cross-cutting rules 1–5), wallet auto-creation at student onboarding, concurrency test

### [x] B. Pooled funds
- Models: `PooledFund` (own `pooled_fund` wallet), `PooledFundContribution`
- Endpoints: `pooled-funds/` (POST, GET), `pooled-funds/{id}/` (log + total + progress), `/contribute/`, `/close/`, `/disburse/`
- Tests: total == ledger sum, disburse permissions, can't over-disburse

### [x] C. Wallet ops — policy, savings, P2P, card freeze
- Models: `Policy`, `ProductCategory`, `Product`, `P2PTransfer`, `P2PAlert`, `SavingsWithdrawal`; wallet withdrawal window fields
- Services: `get_effective_policy`, `authorize_debit` (full), `move_to_savings`, `move_from_savings`, `withdraw_savings`, `p2p_transfer`, `evaluate_p2p_patterns`
- Endpoints: policies, product-categories, products, `students/{id}/effective-policy/`, `wallets/{id}/savings/move-in|move-out|withdraw/`, `wallets/transfer/`, `students/{id}/p2p-history/`, `p2p-alerts/`, card freeze/unfreeze/report-lost
- Tests: caps, blocked category/item/merchant, override resolution, parents can't loosen, savings moves, window, payout reversal, P2P rules + alert

### [x] D. Canteen POS + offline sync
- Models: `Device`, `PosTransaction`, `PosTransactionItem`; `School`-level offline ceiling setting (on `Policy` school default)
- Device-token auth class; `pos/devices/` register/list/revoke/rotate-token; `pos/cache/` (+`?since=`); `pos/sync/`; `pos/purchase/`; `pos/shortfalls/` + resolve
- Tests: idempotent replay, shortfall flagged, per-item isolation, revoked device, cache scoping, frozen in cache

### [x] E. Fee top-ups — `FeeCategory`, `FeePayment`, `fees/pay/`, CRUD, history
### [x] F. Attendance — `AttendanceRecord`, `attendance/tap/`, `attendance/`, `students/{id}/attendance/`
### [x] G. Merchant network — `Merchant` (+ approvals M2M, per-school settlement wallets), approve/suspend, `merchants/{id}/statement/`, blocked merchants in policy
### [x] H. Disputes & refunds — `Dispute`, raise/list/resolve, refund ≤ original
### [x] I. Notifications — `NotificationEvent`, `NotificationPreference`, `DevicePushToken`, `notify()`, channel backends, low-balance throttle, endpoints, lg/sw translations
### [x] J. Privacy — `privacy/my-data/` (json/csv), `DataRequest`, redaction service
### [x] K. Analytics & reconciliation — read-only endpoints
### [x] L. Seed data — extend `seed_demo`
### [x] M. Testing without devices — `simulate_pos`, `mock_webhook`, `run_recurring_topups`, `docs/TESTING_WITHOUT_DEVICES.md`, `docs/requests/*.http`

(Sections A–C are built in the order listed but the cross-cutting pieces —
system wallets, `authorize_debit`, `notify()` — are introduced in A as thin
versions and completed in C and I, so each commit stays green.)

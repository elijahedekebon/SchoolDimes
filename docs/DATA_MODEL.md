# Data Model

Every model, its fields, and its relationships. Kept current by every part.

## Multi-tenancy

`tenants.School` is the tenant. Every tenant-scoped model below carries its
own `school` FK (denormalized directly onto `Card`, `Wallet`, `LedgerEntry`,
`Student` for query efficiency and consistent scoping — not just reachable
through a join), except:
- `accounts.User.school` is **nullable**: `platform_admin` and not-yet-linked
  parents have no single school.
- `accounts.GuardianVerification` and `content.FinancialLiteracyTip` (which
  supports `school=null` for platform-wide tips) are the two intentional
  exceptions — see their sections below.

---

## `accounts`

### `User` (custom, `AUTH_USER_MODEL`)
| Field | Type | Notes |
|---|---|---|
| email | EmailField, unique | `USERNAME_FIELD` |
| password | (from `AbstractBaseUser`) | hashed by Django |
| role | choice | `parent, student, canteen_staff, merchant_staff, school_admin, platform_admin` |
| school | FK → `tenants.School`, null=True | null for `platform_admin`; can be null for a parent |
| preferred_language | choice | `en, lg, sw` (default `en`) |
| phone_number | CharField, blank | |
| full_name | CharField, blank | |
| is_active, is_staff | Boolean | |
| date_joined | DateTimeField, auto | |

### `GuardianVerification`
KYC-lite guardian identity check (proposal §5).
| Field | Type | Notes |
|---|---|---|
| parent | OneToOne → `User` | `limit_choices_to role=parent` |
| full_name | CharField | |
| id_document_type | choice | `national_id, passport` |
| id_number | CharField | |
| status | choice | `pending, verified, rejected` |
| verified_at | DateTimeField, null | set by `accounts.services.mark_guardian_verification()` |
| created_at, updated_at | DateTimeField | |

---

## `tenants`

### `School`
| Field | Type | Notes |
|---|---|---|
| name | CharField | |
| address | TextField, blank | |
| branding | JSONField | `{logo_url, primary_color}` |
| supported_languages | JSONField (list) | subset of `[en, lg, sw]` |
| policy_defaults | JSONField | spending caps/restrictions defaults; **enforced in Part 2** |
| created_at, updated_at | DateTimeField | |

### `SchoolReferral`
Proposal §9 referral tracking.
| Field | Type | Notes |
|---|---|---|
| referring_school | FK → `School` | `related_name=referrals_made` |
| referred_school | FK → `School` | `related_name=referrals_received`; DB constraint: cannot equal `referring_school` |
| status | choice | `pending, applied, rejected` |
| reward_applied | Boolean | set by `tenants.services.apply_referral_reward()` |
| created_at | DateTimeField | |

---

## `students`

### `Student`
| Field | Type | Notes |
|---|---|---|
| school | FK → `School` | |
| name | CharField | |
| class_name | CharField | e.g. "P4", "S2 Blue" |
| date_of_birth | DateField, null | |
| photo | ImageField, null | `media/students/photos/` |
| guardians | M2M → `User`, through `Guardian` | |
| created_at, updated_at | DateTimeField | |

### `Guardian` (through-model)
| Field | Type | Notes |
|---|---|---|
| parent | FK → `User` | |
| student | FK → `Student` | |
| relationship | choice | `mother, father, guardian, other` |
| is_primary_contact | Boolean | |
| created_at | DateTimeField | |
| *unique* | `(parent, student)` | a parent can't double-link the same student |

Siblings share a guardian by having two `Guardian` rows with the same
`parent`; a student can have >1 guardian by having two rows with the same
`student`.

---

## `cards`

### `Card`
| Field | Type | Notes |
|---|---|---|
| school | FK → `School` | denormalized from `student.school` |
| student | FK → `Student` | |
| card_uid | CharField, unique | NFC id; generated via `cards.services.generate_card_uid()` if not supplied |
| pin_hash | CharField | salted (`django.contrib.auth.hashers`); **never serialized** |
| status | choice | `active, frozen, lost` |
| biometric_enrolled | Boolean | flag only — matching is a Part 3/4 client concern |
| issued_at, updated_at | DateTimeField | |

A "reissue" retires the old row (`status=lost`) and inserts a new `Card` row
for the same student — cards are never mutated in place to change `card_uid`.

---

## `wallets`

### `Wallet`
| Field | Type | Notes |
|---|---|---|
| school | FK → `School` | denormalized from `student.school` |
| student | FK → `Student` | |
| wallet_type | choice | `main, savings` |
| cached_balance | DecimalField(12,2) | **only** written by `wallets.services.post_ledger_entry()` |
| created_at, updated_at | DateTimeField | |
| *unique* | `(student, wallet_type)` | every student gets exactly one of each |

`Wallet.balance` is a Python property returning `cached_balance`.
`wallets.services.compute_balance(wallet)` independently re-sums
`LedgerEntry` rows — used by tests/reconciliation to catch any drift.

### `LedgerEntry`
Append-only. The **only** way money or balances change anywhere in the system.
| Field | Type | Notes |
|---|---|---|
| school | FK → `School` | denormalized from `wallet.school` |
| wallet | FK → `Wallet`, `on_delete=PROTECT` | |
| amount | DecimalField(12,2) | `>= 0.01` |
| direction | choice | `credit, debit` |
| entry_type | choice | see list in `API_CONTRACTS.md` |
| reference_id | CharField, blank | id of the source object (POS sale, transfer, etc.) |
| description | CharField, blank | |
| created_at | DateTimeField, auto | |

Admin site disables add/change/delete on `LedgerEntry` as a safety rail;
the actual invariant is enforced by *always* going through
`post_ledger_entry()`, which locks the wallet row (`select_for_update`)
inside a transaction and raises `core.exceptions.InsufficientFundsError`
rather than letting a debit take a wallet negative.

### `SavingsGoal`
| Field | Type | Notes |
|---|---|---|
| wallet | FK → `Wallet` | must be `wallet_type=savings` (validated) |
| goal_name | CharField | |
| target_amount | DecimalField(12,2) | |
| target_date | DateField, null | |
| created_at | DateTimeField | |

Moving money into/out of a goal (crediting/debiting the savings wallet) is a
ledger operation for **Part 2** — this model is data-only in Part 1.

---

## `content`

### `FinancialLiteracyTip`
| Field | Type | Notes |
|---|---|---|
| school | FK → `School`, null=True | `null` = platform-wide tip |
| title | CharField | |
| body | TextField | |
| language | choice | `en, lg, sw` |
| target_age_range | CharField, blank | e.g. "6-9" |
| created_at, updated_at | DateTimeField | |

**Translation model:** each language is its own row (see `DECISIONS.md`) —
not per-field i18n via `modeltranslation` or similar.

---

## Entity relationship summary

```
School 1──* User (school_admin/canteen_staff/merchant_staff; null for platform_admin/parent)
School 1──* Student
School 1──* Card, Wallet, LedgerEntry, FinancialLiteracyTip (nullable)
School *──* School (via SchoolReferral: referring/referred)

User(parent) *──* Student   (through Guardian)
User(parent) 1──1 GuardianVerification

Student 1──* Card   (historical: many over time, one active)
Student 1──2 Wallet (exactly one main + one savings)

Wallet 1──* LedgerEntry
Wallet(savings) 1──* SavingsGoal
```

---

# Part 2 additions

## Chart of wallets (double entry)

Since Part 2 every money movement is a **transfer between two wallets of the
same school**, posted by `wallets.services.post_transfer()` as two
`post_ledger_entry()` calls sharing a `reference_id`. Invariants the tests
assert (`conftest.assert_books_balanced`): each wallet's `cached_balance`
equals its ledger re-sum; debits and credits under each `reference_id` are
equal; **the sum of all wallet balances in a school is exactly 0**.

| `wallet_type` | Owner | Normal balance | Meaning |
|---|---|---|---|
| `main` | student | ≥ 0 | spendable pocket money |
| `savings` | student | ≥ 0 | savings |
| `aggregator_clearing` | school (exactly one) | **≤ 0** | money the payment aggregator holds for the school. The only wallet allowed to go negative. Deposits debit it, payouts credit it |
| `school_settlement` | school (exactly one) | ≥ 0 | canteen sales, fee payments, pooled-fund disbursements to the school |
| `pooled_fund` | one `PooledFund` | ≥ 0 | a group collection pot |
| `merchant_settlement` | one (merchant, school) pair | ≥ 0 | what a nearby merchant earned from that school's students |

| Movement | Debit | Credit | `entry_type` (debit side / credit side) | `reference_id` |
|---|---|---|---|---|
| Deposit confirmed | aggregator_clearing | student main/savings | `deposit` | `deposit:<Deposit.id>` |
| Gift voucher paid (auto-redeemed) | aggregator_clearing | student main | `gift_voucher` | `deposit:<id>` |
| Pooled-fund contribution | aggregator_clearing | pooled_fund | `pooled_fund_contribution` | `deposit:<id>` |
| Payout started (savings withdrawal / external disbursement) | source wallet | aggregator_clearing | `savings_withdrawal` / `pooled_fund_disbursement` | `payout:<Payout.id>` |
| Payout failed (compensation) | aggregator_clearing | source wallet | `reversal` | `payout:<id>` |
| Part 1 legacy history (migration `wallets.0003`) | clearing or student | student or settlement | original type | `legacy:<original entry id>` |
| Seed data | as above | | | `seed:<student>:<what>` |

Later sections add their rows below under "Chart of wallets — continued".

## `core`

### `AuditLog`
Append-only record of privileged writes; every platform_admin write into a
school's data goes through `core.audit.audit()` (or the
`AuditPlatformAdminWritesMixin` viewset mixin).

| Field | Type | Notes |
|---|---|---|
| actor | FK → User, null | |
| actor_role | CharField | role at the time |
| school | FK → School, null | tenant written into |
| action | CharField | e.g. `policy.update` |
| target_type, target_id | CharField | model name + pk |
| details | JSONField | |
| created_at | DateTimeField | |

## `wallets` — Part 2 changes (approved, additive)

`Wallet`:
- `student` is now **nullable** (null ⇔ system wallet).
- `wallet_type` max_length 10 → 24; new values `school_settlement`,
  `aggregator_clearing`, `pooled_fund`, `merchant_settlement`.
- DB check `wallet_student_matches_type`: main/savings ⇔ `student` set.
- DB unique `one_school_system_wallet_per_type`: one `school_settlement` and
  one `aggregator_clearing` per school.
- `is_system` property.

`LedgerEntry.entry_type` adds `reversal`, `shortfall_recovery`.

`post_ledger_entry()` adds `allow_negative=False` (honoured only on
`aggregator_clearing`, anything else raises `InvalidWalletTypeError`), rejects
amounts ≤ 0, and fires the signal `wallets.signals.ledger_entry_posted`
(`entry`, `balance_after`) after each entry. Existing callers are unaffected.

New helpers in `wallets/services.py`: `post_transfer()`, `get_system_wallet()`,
`get_student_wallet()`, `ensure_student_wallets()` (now called when a
student is created via the API), `school_books_total()`.

## `payments`

### `Deposit`
One model for every collection (money in), so there is one confirmation path.

| Field | Type | Notes |
|---|---|---|
| school | FK → School | from the target wallet |
| purpose | choice | `wallet_topup, gift_voucher, pooled_fund_contribution` |
| wallet | FK → Wallet (PROTECT) | target: student main/savings, or a `pooled_fund` wallet |
| amount | Decimal(12,2) | > 0 and ≤ `MAX_TRANSACTION_AMOUNT` |
| channel | choice | `momo, bank, ussd` |
| payer_phone | CharField | |
| status | choice | `pending, confirmed, failed, expired` |
| reference | CharField, **unique** | ours; prefix `SD-DEP-`, `SD-GV-`, `SD-PF-` |
| aggregator_ref | CharField, **unique**, null | the aggregator's id |
| instructions | JSON | channel instructions for the payer (see API) |
| initiated_by | FK → User, null | parent; null for public contributors |
| contributor | FK → Contributor, null | |
| recurring_topup | FK → RecurringTopUp, null | set for scheduled runs |
| idempotency_key | CharField, **unique** | client-supplied; `recurring:<id>:<YYYYmmddTHHMM>` for scheduled runs |
| failure_reason | CharField | `declined, expired, aggregator_error, …` |
| created_at, confirmed_at, updated_at | DateTimeField | |

### `Payout`
Money out to a phone. The source wallet is debited when the payout starts; a
failure posts a `reversal` transfer back (nothing is deleted).

| Field | Type | Notes |
|---|---|---|
| school | FK → School | |
| purpose | choice | `savings_withdrawal, pooled_fund_disbursement` |
| source_wallet | FK → Wallet | |
| amount | Decimal(12,2) | |
| phone_number | CharField | |
| description | CharField | |
| status | choice | `pending, succeeded, failed` |
| reference | CharField, unique | `SD-PO-…` |
| aggregator_ref | CharField, unique, null | |
| idempotency_key | CharField, unique, null | |
| requested_by | FK → User, null | |
| failure_reason | CharField | |
| created_at, completed_at | DateTimeField | |

### `Contributor`
`name, phone_number, email, relationship_label, created_at`. No account and no
school FK (reached through its deposits). One row per contribution.

### `StudentTopUpLink`
`school, student, wallet (main), token (unique; 32 random bytes urlsafe),
created_by (parent), active, expires_at (null), revoked_at (null), created_at`.

### `GiftVoucher`
`school, sender_user (null), sender_contributor (null), student, wallet
(main), amount, message (≤ 280), status (pending_payment | paid | redeemed |
cancelled), deposit (1:1 → Deposit), redeemed_at, created_at`.

### `RecurringTopUp`
`school, parent, student, wallet (main), amount, channel, payer_phone,
frequency (weekly | monthly), day_of_week (0 = Monday … 6), day_of_month
(1 … 28), next_run_at (UTC, server-computed), active, last_run_at,
last_status (pending | succeeded | failed | guardian_unlinked),
consecutive_failures, created_at, updated_at`.

### `UnmatchedWebhook`
`reference, aggregator_ref, reason (unknown_reference | amount_mismatch |
late_success_after_failure), payload (JSON), reviewed, received_at`. Reviewed
in Django admin.

## `notifications`

### `NotificationEvent`
| Field | Type | Notes |
|---|---|---|
| user | FK → User | recipient |
| event_type | CharField | a key of `notifications/templates.py` |
| payload | JSON | machine-readable data for clients (ids, amounts, actions) |
| channel | choice | `in_app, sms, push` |
| title, body | Char / Text | rendered once, in the recipient's `preferred_language` |
| status | choice | `pending, sent, logged (stub backend), failed` |
| error | CharField | |
| sent_at, read_at, created_at | DateTimeField | |

### `NotificationPreference`
`user (1:1), in_app_enabled, sms_enabled (default false), push_enabled
(default true), low_balance_thresholds (JSON {"<student_id>": "2000.00"}),
updated_at`.

### `DevicePushToken`
`user, token (unique), platform (android | ios | web), created_at, last_used_at`.

## `pooled_funds` — Section B

### `PooledFund`
| Field | Type | Notes |
|---|---|---|
| school | FK → School | |
| title | CharField | |
| purpose | TextField | |
| group_label | CharField | class/group, e.g. "P4 Blue" |
| created_by | FK → User | parent or school_admin |
| target_amount | Decimal, null | |
| deadline | Date, null | contributions refused after it |
| status | choice | `open, closed, disbursed` |
| wallet | 1:1 → Wallet (`pooled_fund`) | holds the money |
| created_at, closed_at | DateTime | |

### `PooledFundContribution`
Created only when the pooled-fund Deposit is **confirmed**.
`fund, contributor_user (null), contributor (→ payments.Contributor, null),
amount, deposit (1:1), created_at`.

### `PooledFundDisbursement`
`fund, amount, destination (school_settlement | external), description,
payout (1:1 → payments.Payout, null), disbursed_by, created_at`.

### Chart of wallets — continued
| Movement | Debit | Credit | entry_type | reference_id |
|---|---|---|---|---|
| Disbursement to school | pooled_fund | school_settlement | `pooled_fund_disbursement` | `pooled:<fund>:<disbursement>` |
| External disbursement | pooled_fund | aggregator_clearing | `pooled_fund_disbursement` | `payout:<id>` |

## `policies` — Section C

### `ProductCategory`
`school, name (unique per school), is_unhealthy (analytics nutrition flag),
active, created_at, updated_at`.

### `Product`
`school, name, category (→ ProductCategory, PROTECT), price, active,
created_at, updated_at`. (Section G adds `merchant`.)

### `Policy`
| Field | Type | Notes |
|---|---|---|
| school | FK → School | |
| student | 1:1 → Student, null | null = the school default (DB-unique per school) |
| daily_spend_cap, weekly_spend_cap, per_transaction_cap, p2p_daily_cap | Decimal, null | null = no limit / inherit |
| p2p_enabled | Boolean, null | null = inherit (default row: null = enabled) |
| low_balance_threshold | Decimal, null | alert level, not a limit |
| blocked_categories, allowed_categories | M2M → ProductCategory | empty allow-list = all allowed |
| blocked_items | M2M → Product | |
| updated_by | FK → User, null | |
| created_at, updated_at | DateTime | |

`School.policy_defaults` (Part 1 JSON) is **superseded**: migration
`policies.0002` copied its recognised scalar keys into each school's default
row. The field stays in the schema and API but nothing reads it any more.

## `wallets` — Section C additions
- `Wallet.withdrawal_window_start`, `Wallet.withdrawal_window_end`
  (DateTime, null; used on savings wallets).
- `SavingsGoal.reached_at` (DateTime, null).

### `P2PTransfer`
`school, sender_wallet, recipient_wallet (both student main wallets), amount,
note, initiated_by (guardian, null), device_id_ref (POS device id, null),
created_at`.

### `P2PAlert`
`school, student, rule (many_distinct_senders | repeated_near_cap), details
(JSON), status (open | reviewed | dismissed), reviewed_by, reviewed_at,
review_notes, created_at`. At most one open alert per (student, rule), by
application rule.

### Chart of wallets — continued
| Movement | Debit | Credit | entry_type (debit / credit) | reference_id |
|---|---|---|---|---|
| Savings move-in | main | savings | `savings_move_out` / `savings_move_in` | `savings:<random>` |
| Savings move-out | savings | main | `savings_move_out` / `savings_move_in` | `savings:<random>` |
| Savings withdrawal | savings | aggregator_clearing | `savings_withdrawal` | `payout:<id>` |
| P2P | sender main | recipient main | `p2p_transfer_out` / `p2p_transfer_in` | `p2p:<id>` |

## `tenants` — Section D addition

### `SchoolSettings`
One per school (created lazily). `school (1:1), offline_spend_ceiling
(Decimal, default 2000), pin_lockout_threshold (default 5),
device_stale_after_hours (default 24), attendance_notify_guardians (default
false), attendance_on_canteen_devices (default false), updated_at`.

## `pos` — Section D

### `Device`
| Field | Type | Notes |
|---|---|---|
| school | FK → School | registering school (tenant owner of the record) |
| merchant | FK → merchants.Merchant, null | Section G; merchant devices only |
| device_name | CharField | |
| device_role | choice | `canteen, merchant, attendance` |
| token_hash | CharField(64), unique | SHA-256 of the raw token; raw token never stored |
| token_prefix | CharField(8) | display only |
| status | choice | `active, revoked` |
| last_seen_at, last_sync_at | DateTime, null | heartbeat / last successful sync |
| app_version | CharField | from `X-App-Version` |
| registered_by | FK → User | |
| created_at, revoked_at | DateTime | |

### `PosTransaction`
| Field | Type | Notes |
|---|---|---|
| device | FK → Device | |
| school | FK → School | the **card holder's** school |
| merchant | FK → Merchant, null | Section G |
| card, student, wallet | FK, null | null only for rejected unknown cards |
| card_uid | CharField | as sent |
| channel | choice | `offline_sync, online` |
| amount | Decimal | sale total as rung up |
| applied_amount | Decimal | actually debited |
| shortfall_amount | Decimal | amount − applied_amount |
| recovered_amount | Decimal | collected later by recovery |
| idempotency_key | CharField | **unique per device** (DB constraint) |
| device_local_timestamp | DateTime | |
| received_at | DateTime | |
| sync_status | choice | `applied, shortfall, rejected` (`duplicate` is only a response status) |
| reject_reason | CharField | |
| flags | JSON list | rule codes broken by an offline sale |
| pin_verified | Boolean, null | as reported |
| ledger_reference | CharField | `pos:<id>` |
| review_status | choice | `none, pending, recovery_pending, resolved` |
| resolution | choice | `accept, write_off, recover_from_next_topup, charge_guardian` |
| reviewed_by, reviewed_at, review_notes | | |

### `PosTransactionItem`
`transaction, product (null), description, category (null), quantity,
unit_price, line_total`.

### `PinFailureReport`
`device, card, failed_attempts, device_local_timestamp, received_at`.

## `wallets` — Section D addition
`P2PTransfer.idempotency_key` (unique, null): set by POS-initiated transfers.

### Chart of wallets — continued
| Movement | Debit | Credit | entry_type | reference_id |
|---|---|---|---|---|
| Canteen sale | student main | school_settlement | `pos_purchase` | `pos:<id>` |
| Shortfall recovery | student main | the sale's settlement wallet | `shortfall_recovery` | `recovery:<txn>:<n>` |

## `fees` — Section E

### `FeeCategory`
`school, name, amount_type (fixed | range), fixed_amount, min_amount,
max_amount, active, due_date (null), applicable_classes (JSON list of
class_name; empty = all), created_at, updated_at`.

### `FeePayment`
`school, student, fee_category, amount, paid_by (User), ledger_reference
(fee:<id>), status (completed), idempotency_key (unique, null), created_at`.
Only completed payments are stored; refusals are returned to the caller.

### Chart of wallets — continued
| Movement | Debit | Credit | entry_type | reference_id |
|---|---|---|---|---|
| Fee payment | student main | school_settlement | `fee_payment` | `fee:<id>` |

## `attendance` — Section F

### `AttendanceRecord`
`school, student, card (null), device (→ pos.Device), direction (in | out),
device_local_timestamp, received_at, idempotency_key`. Unique
`(device, idempotency_key)`. Indexed on `(school, device_local_timestamp)`.

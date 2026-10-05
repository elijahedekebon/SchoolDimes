# API Contracts

Single source of truth for every SchoolDimes endpoint. Every part appends to
this file rather than maintaining its own copy. All endpoints are under
`/api/v1/`. All JSON fields are `snake_case`, matching Django model field
names exactly. Auth is JWT (`Authorization: Bearer <access>`), issued by
Part 1's `accounts` app.

Tenant scoping is always derived server-side from the authenticated user
(`request.user.school`, or the set of students a parent is linked to via
`Guardian`) -- a client can never pick a `school` id and see another
tenant's data, except `platform_admin`, who legitimately operates across
tenants.

---

## Part 1 — Foundation

### Auth (`accounts` app)

#### `POST /api/v1/auth/login`
Body: `{ "email": str, "password": str }`
Response `200`: `{ "access": str, "refresh": str }`
The JWT carries extra claims: `role`, `school_id`, `preferred_language`.

#### `POST /api/v1/auth/refresh`
Body: `{ "refresh": str }`
Response `200`: `{ "access": str, "refresh": str }` (refresh rotation is on;
the old refresh token is blacklisted).

#### `POST /api/v1/auth/logout`
Auth required. Body: `{ "refresh": str }`
Response `205`. Blacklists the given refresh token. `400` if missing/invalid.

#### `GET /api/v1/me`
Auth required. Returns the caller's own `User` profile.
Response `200`: `{ id, email, full_name, role, school, preferred_language, phone_number, date_joined }`

#### `PATCH /api/v1/me`
Auth required. Editable fields: `full_name`, `preferred_language`, `phone_number`.
`role` and `school` are read-only (never settable by the user themselves).

#### `GET|POST /api/v1/guardian-verifications/`
Auth required.
- `parent`: sees/creates only their own verification.
- `school_admin`: sees verifications for parents linked (via `Guardian`) to a student in their school.
- `platform_admin`: sees all.
Create body: `{ full_name, id_document_type, id_number }` (parent is inferred from the token).
Response fields: `{ id, parent, parent_email, full_name, id_document_type, id_number, status, verified_at, created_at, updated_at }`.
`status` starts `pending`; only `school_admin`/`platform_admin` can change it via `PATCH`.

#### `PATCH /api/v1/guardian-verifications/{id}/`
Same visibility rules as above. A parent may edit their own submission only
while it is still `pending`; only admins may set `status`.

---

### Tenants (`tenants` app)

#### `GET|POST|PATCH|PUT|DELETE /api/v1/schools/`
`platform_admin` only, full CRUD.
Fields: `{ id, name, address, branding, supported_languages, policy_defaults, created_at, updated_at }`.
- `branding`: `{ "logo_url": str, "primary_color": "#rrggbb" }`
- `supported_languages`: subset of `["en", "lg", "sw"]`
- `policy_defaults`: spending caps / category restrictions / blocked items applied to new cards at this school. **Enforcement is Part 2** — Part 1 only stores the shape.

#### `GET|POST|PATCH|PUT|DELETE /api/v1/school-referrals/`
- `platform_admin`: full CRUD, sees all.
- `school_admin`: read-only, sees referrals where their school is either party.
- Others: empty list.
Fields: `{ id, referring_school, referred_school, status, reward_applied, created_at }`.

#### `POST /api/v1/school-referrals/{id}/apply/`
`platform_admin` only. Marks the referral `applied` and `reward_applied=true`.
**The actual billing/discount mechanics are a placeholder** — see `docs/DECISIONS.md`.

---

### Students (`students` app)

#### `GET|POST|PATCH|PUT|DELETE /api/v1/students/`
- `parent`: sees only students they are linked to via `Guardian`.
- `school_admin`/`canteen_staff`/`merchant_staff`: sees students in their own school.
- `platform_admin`: sees all; optional `?school=<id>` filter.
- Create/update/delete: `school_admin`/`platform_admin` only.
Fields: `{ id, school, name, class_name, date_of_birth, photo, created_at, updated_at }`.
`school` is read-only in the request body (server-derived) for all roles except `platform_admin`.

#### `GET|POST|PATCH|PUT|DELETE /api/v1/guardians/`
Through-model linking a parent `User` to a `Student`.
- `parent`: sees only their own links.
- `school_admin`/`platform_admin`: manage links (create/update/delete).
- `canteen_staff`/`merchant_staff`: read-only, own school.
Fields: `{ id, parent, student, relationship, is_primary_contact, created_at }`.
`relationship` ∈ `mother | father | guardian | other`. `(parent, student)` is unique.

---

### Cards (`cards` app)

Card `pin_hash` is **never** serialized in any response.

#### `GET /api/v1/cards/` / `GET /api/v1/cards/{id}/`
Same visibility rules as students (parent → own students' cards; staff → own
school; platform_admin → all).
Fields: `{ id, school, student, card_uid, status, biometric_enrolled, issued_at, updated_at }`.
`status` ∈ `active | frozen | lost`.

#### `POST /api/v1/cards/issue/`
`school_admin`/`platform_admin` only. Body: `{ "student": <id>, "pin": "1234" }` (4-6 digits).
Response `201`: the new `Card`. `403` if issuing for a student outside your school (non-platform-admin).

#### `POST /api/v1/cards/{id}/reissue/`
`school_admin`/`platform_admin` only. Body: `{ "pin": "5678" }`.
Retires the old card (`status=lost`) and issues a fresh one (new `card_uid`) for the same student.
Response `201`: the new `Card`.

#### `POST /api/v1/cards/{id}/freeze/`
#### `POST /api/v1/cards/{id}/unfreeze/`
Usable by: `platform_admin`, the card's own `school_admin`, or a `parent`
linked to the card's student via `Guardian`. `403` otherwise.
Response `200`: the updated `Card`.

---

### Wallets (`wallets` app)

Every student has exactly one `main` and one `savings` `Wallet`, created by
the seed script in Part 1 (Part 2 will create them at student-onboarding time).
`Wallet.balance`/`cached_balance` is **never** written directly — it only
changes via `wallets.services.post_ledger_entry()`.

#### `GET /api/v1/wallets/` / `GET /api/v1/wallets/{id}/`
Same visibility rules as students.
Fields: `{ id, school, student, wallet_type, balance, created_at, updated_at }`.
`wallet_type` ∈ `main | savings`.

#### `GET /api/v1/wallets/{id}/balance/`
Response `200`:
```json
{
  "wallet": { "...WalletSerializer fields..." },
  "balance": "700.00",
  "history": {
    "count": 3,
    "next": null,
    "previous": null,
    "results": [
      { "id": 1, "wallet": 1, "amount": "300.00", "direction": "debit",
        "entry_type": "pos_purchase", "reference_id": "", "description": "...",
        "created_at": "2026-01-01T10:00:00Z" }
    ]
  }
}
```
`history` is paginated (`?page=`, `?page_size=`, default page size 20, max 100).

#### `GET|POST|PATCH|PUT|DELETE /api/v1/savings-goals/`
Scoped like wallets (a savings goal is only visible/editable if its wallet is).
Fields: `{ id, wallet, goal_name, target_amount, target_date, created_at }`.
`wallet` must point at a `wallet_type=savings` wallet (validated).
**Moving money into/out of a goal is a ledger operation — Part 2.**

`LedgerEntry.entry_type` choices (extensible): `deposit, pos_purchase,
p2p_transfer_out, p2p_transfer_in, savings_move_in, savings_move_out,
savings_withdrawal, refund, fee_payment, gift_voucher,
pooled_fund_contribution, pooled_fund_disbursement`. Ledger entries are
read-only via the API in Part 1 (no create/update/delete endpoint) — they
are only ever produced server-side by service functions that later parts
will expose through their own endpoints (deposits, POS sales, transfers, etc).

---

### Content (`content` app)

#### `GET|POST|PATCH|PUT|DELETE /api/v1/financial-literacy-tips/`
- Anyone authenticated: list/read tips that are either global (`school=null`)
  or belong to their own school. Optional `?language=en|lg|sw` filter.
- `school_admin`: create/edit tips scoped to their own school (`school` is
  auto-assigned server-side, cannot be overridden).
- `platform_admin`: create/edit any tip, including global ones (`school=null`).
Fields: `{ id, school, title, body, language, target_age_range, created_at, updated_at }`.
Note: translation is done via **separate rows per language**, not per-field
i18n — "the same tip" in en/lg/sw is three rows sharing a topic, not one row
with three text columns. See `docs/DECISIONS.md`.

---

## Deferred to later parts (do not build against these paths yet)

- ~~Deposits, P2P, POS purchases, fee top-ups, pooled funds, gift vouchers,
  recurring top-ups, attendance, merchant network, disputes~~ — **built in
  Part 2, see below.**
- POS Android app — **Part 3** (the server side is Part 2 Section D).
- Parent/admin dashboards, offline mode/sync, biometric matching (the
  `Card.biometric_enrolled` flag exists now; actual capture/matching is a
  client concern) — **Part 4**.

---

## Part 2 — Money movement & operations

### Part 2 conventions (apply to every endpoint below)

- **Paths.** Shown with Part 1's trailing slash. Every Part 2 route also
  accepts the same path without the slash (`/api/v1/pos/sync` ==
  `/api/v1/pos/sync/`).
- **Auth types.**
  - `JWT` — `Authorization: Bearer <access>` (Part 1 login).
  - `Device` — `Authorization: Device <raw device token>` (Section D). Used
    by every `/pos/…` device endpoint and `/attendance/tap/`. Never a JWT.
  - `Public` — no auth; rate-limited per IP (`PUBLIC_TOPUP_THROTTLE_RATE`,
    default `20/min`; `429` when exceeded).
  - `Signature` — the aggregator webhook only.
- **Amounts** are decimal strings with ≤ 2 dp, UGX (e.g. `"5000.00"`). A
  request amount must be `> 0` and `≤ MAX_TRANSACTION_AMOUNT` (default
  5,000,000). Direction always comes from the endpoint, never from a sign.
- **Business-rule errors** share one body shape:
  `{"code": "<snake_case_reason>", "detail": "<translated message>"}`, with
  `400` (bad input), `404` (not found **or not yours** — other tenants' and
  other families' objects are always 404, never 403), `409` (idempotency or
  state conflict) or `422` (debit refused). Field validation errors keep
  DRF's default `{"field": ["msg"]}` with `400`.
  Common codes: `amount_invalid`, `amount_too_large`,
  `idempotency_key_required`, `idempotency_conflict`, `not_found`,
  `channel_invalid`, `phone_number_required`, `schedule_invalid`, plus the
  debit refusal codes listed under Section C.
- **Idempotency.** Every create that can be retried over a flaky network takes
  an `idempotency_key` (client-generated, ≤ 128 chars; use a UUID), unique in
  the database. Retrying with the same key returns the original object with
  `200` instead of `201`; reusing a key for a *different* request returns
  `409 idempotency_conflict`.
- **Ledger references.** Every `LedgerEntry` created in Part 2 has
  `reference_id = "<kind>:<id>"`, shared by both sides of the transfer:
  `deposit:<Deposit.id>`, `payout:<Payout.id>`, `pos:<PosTransaction.id>`,
  `p2p:<P2PTransfer.id>`, `fee:<FeePayment.id>`, `savings:<id>`,
  `pooled:<PooledFund.id>:<n>`, `refund:<Dispute.id>`,
  `recovery:<PosTransaction.id>:<n>`.
- **Pagination** as in Part 1: `{count, next, previous, results}`, `?page=`,
  `?page_size=` (≤ 100).
- **Time.** Timestamps are ISO-8601 UTC. Day-based rules (daily caps,
  "today", reports) use Africa/Kampala calendar days.

### Payments (`payments` app) — Section A

#### `POST /api/v1/payments/deposits/`
JWT, **parent** only. Tops up a wallet of one of the caller's linked students.
NO money moves until the aggregator confirms via the webhook.
Body:
```json
{ "wallet": 12, "amount": "5000", "channel": "momo",
  "payer_phone": "0772000111", "idempotency_key": "6f1c…uuid" }
```
`channel` ∈ `momo | bank | ussd`. `payer_phone` defaults to the parent's
`phone_number`. `wallet` must be a main or savings wallet of a linked student
(otherwise `404 not_found`).
Response `201` (or `200` on idempotent replay) — a Deposit:
```json
{ "id": 7, "school": 1, "purpose": "wallet_topup", "wallet": 12, "student": 4,
  "amount": "5000.00", "channel": "momo", "payer_phone": "0772000111",
  "status": "pending", "reference": "SD-DEP-9F2A…", "aggregator_ref": "MOCK-1A2B…",
  "instructions": { "type": "momo_prompt", "phone_number": "0772000111",
                    "message": "Approve the payment of UGX 5,000 on your phone …" },
  "initiated_by": 3, "contributor": null, "contributor_name": null,
  "recurring_topup": null, "idempotency_key": "6f1c…uuid",
  "failure_reason": "", "created_at": "…", "confirmed_at": null }
```
`instructions.type` is one of:
- `momo_prompt` — `{phone_number, message}`
- `ussd` — `{ussd_code, message}`
- `bank_transfer` — `{bank_name, account_name, account_number, narration, message}`

If the aggregator declines at initiation, the deposit comes back with
`status: "failed"` and a `failure_reason` (e.g. `declined`). In mock mode,
payer phones ending in `999` are declined.

#### `GET /api/v1/payments/deposits/{id}/`
JWT. Status polling: the parent app polls until `status` ≠ `pending`.
Visible to the initiator, guardians of the target student, that school's
school_admin, and platform_admin. Everyone else gets `404`.

#### `GET /api/v1/payments/deposits/`
JWT. Parent: deposits into their linked students' wallets, plus any deposit
they initiated (e.g. pooled-fund contributions). school_admin: their school.
Filters: `?student=<id>`, `?status=`, `?purpose=`. Paginated Deposits.

#### `GET|POST /api/v1/payments/topup-links/`, `GET /api/v1/payments/topup-links/{id}/`
JWT, **parent** only; links for their own linked students only.
Create body: `{ "student": 4, "expires_at": "2026-12-31T00:00:00Z" }` (`expires_at` optional).
Response `201`:
```json
{ "id": 2, "student": 4, "wallet": 12, "token": "Qm9…(43 chars)",
  "share_url": "http://localhost:8000/topup/Qm9…", "active": true,
  "expires_at": null, "revoked_at": null, "created_at": "…" }
```
A student who isn't linked to the caller → `404`.

#### `POST /api/v1/payments/topup-links/{id}/revoke/`
JWT, the parent who owns the link. Response `200`: the link with
`active: false` and `revoked_at` set. The token stops working immediately.

#### `GET /api/v1/public/topup-links/{token}/`
**Public**, throttled. Response `200` — exactly these two fields and nothing else:
```json
{ "student_first_name": "Amina", "school_name": "Kampala Demo Primary School" }
```
Unknown, revoked and expired tokens all return the same
`404 {"code": "not_found", …}`.

#### `POST /api/v1/public/topup-links/{token}/deposits/`
**Public**, throttled. A contributor tops up the linked student's main wallet.
```json
{ "contributor": { "name": "Jjajja Nalongo", "phone_number": "0701000222",
                   "email": "", "relationship_label": "Grandmother" },
  "amount": "3000", "channel": "ussd", "payer_phone": "0701000222",
  "idempotency_key": "uuid" }
```
`contributor.name` is required, plus a `phone_number` or an `email`.
Response `201`/`200` — a restricted Deposit view with no wallet or student ids:
`{ reference, amount, channel, status, instructions, failure_reason, created_at, confirmed_at }`.
On confirmation, every guardian of the student gets a
`contributor_topup_received` notification.

#### `GET /api/v1/public/topup-links/{token}/deposits/{reference}/`
**Public**, throttled. Polls a contributor deposit made through this link.
Same restricted shape.

#### `POST /api/v1/public/topup-links/{token}/gift-vouchers/`
**Public**, throttled. Same body as the contributor deposit, plus
`"message"` (≤ 280 chars). Response `201`/`200`:
`{ amount, message, status, deposit: {restricted deposit}, created_at }`.

#### `GET|POST /api/v1/payments/gift-vouchers/`, `GET /api/v1/payments/gift-vouchers/{id}/`
JWT. Create: **parent**, for a linked student only.
```json
{ "student": 4, "amount": "2500", "message": "Happy birthday!",
  "channel": "momo", "payer_phone": "0772000111", "idempotency_key": "uuid" }
```
Response `201`/`200`:
```json
{ "id": 1, "school": 1, "student": 4, "wallet": 12, "amount": "2500.00",
  "message": "Happy birthday!", "status": "pending_payment", "sender_user": 3,
  "sender_contributor": null, "sender_name": "Moses Parent", "deposit": 9,
  "deposit_reference": "SD-GV-…", "deposit_status": "pending",
  "instructions": {…}, "redeemed_at": null, "created_at": "…" }
```
`status` goes `pending_payment → redeemed` when payment is confirmed: the
voucher auto-redeems into the main wallet (`entry_type=gift_voucher`) and
guardians get a `gift_received` notification that includes the message. It
goes `→ cancelled` if the payment fails. List: a parent sees vouchers to
their students and vouchers they sent; school_admin sees their school's.

#### `GET|POST /api/v1/payments/recurring-topups/`, `GET|PATCH|PUT|DELETE /api/v1/payments/recurring-topups/{id}/`
JWT. Writes: **parent** only, for their own schedules and linked students.
Reads: the parent (own schedules), school_admin (their school).
```json
{ "student": 4, "amount": "4000", "channel": "momo", "payer_phone": "0772000111",
  "frequency": "weekly", "day_of_week": 0, "day_of_month": null, "active": true }
```
Weekly needs `day_of_week` 0 (Mon) … 6 (Sun); monthly needs `day_of_month`
1 … 28 (otherwise `400 schedule_invalid`). The run time is
`RECURRING_TOPUP_RUN_HOUR` (default 08:00) Africa/Kampala. Responses also carry
the read-only fields `id, school, parent, wallet, next_run_at, last_run_at,
last_status, consecutive_failures, created_at, updated_at`. Changing the
schedule, or setting `active: true` on a paused schedule, recomputes
`next_run_at`; re-activating also resets `consecutive_failures`.
Execution: Celery Beat every 15 min (`payments.tasks.run_recurring_topups`),
or `manage.py run_recurring_topups`. After `RECURRING_TOPUP_MAX_FAILURES`
(default 3) consecutive failures, the schedule is set to `active: false` and the
parent gets `recurring_topup_paused`.

#### `POST /api/v1/payments/webhook/`
**Signature** auth. In mock mode the header is
`X-SchoolDimes-Signature: hex(HMAC-SHA256(PAYMENT_AGGREGATOR_WEBHOOK_SECRET, raw body))`;
a real aggregator's client verifies that provider's own scheme. Normalised body:
```json
{ "reference": "SD-DEP-…", "aggregator_ref": "MOCK-…", "status": "successful",
  "amount": "5000.00", "failure_reason": "" }
```
The `reference` prefix routes the event: `SD-DEP-`, `SD-GV-` and `SD-PF-` go to
the Deposit; `SD-PO-` goes to a Payout. All of them go through one service,
`payments.services.process_payment_event()`.
Responses: `401 bad_signature`, `400 bad_payload`; otherwise always `200`
`{"status": "confirmed" | "failed" | "duplicate" | "unmatched" | "payout_succeeded" | "payout_failed"}`.
A replay returns `duplicate` and moves no money. Unknown references, amount
mismatches, and a success after a recorded failure return `unmatched`: they are
logged in `UnmatchedWebhook` for admin review and answered `200` so the
aggregator stops retrying. A success for an `expired` deposit still confirms it,
because the payer was charged.

### Pooled funds (`pooled_funds` app) — Section B

Visibility for every endpoint: parents see funds of the schools their linked
students attend; school staff see their own school's; platform_admin sees all.
Anything else is `404`.

#### `GET /api/v1/pooled-funds/`
JWT. Optional `?status=open|closed|disbursed`. Paginated list of:
```json
{ "id": 3, "school": 1, "title": "P4 trip to Entebbe Zoo", "purpose": "Bus + tickets",
  "group_label": "P4", "created_by": 5, "target_amount": "20000.00",
  "deadline": "2026-11-30", "status": "open", "wallet": 41,
  "total_contributed": "12000.00", "balance": "12000.00", "progress_percent": 60.0,
  "created_at": "…", "closed_at": null }
```
`total_contributed`, `balance` and `progress_percent` are computed from the
**ledger of the fund's wallet** on every request (never stored), so they
always equal the ledger. `progress_percent` is `null` when there is no target,
and is capped at 100.

#### `POST /api/v1/pooled-funds/`
JWT, **parent** or **school_admin**. Body: `{ title, purpose?, group_label?,
target_amount?, deadline?, school? }`. `school` is only needed by a parent
whose children attend more than one school (`400 school_required`). It must
be one of the caller's own schools (else `404`). Response `201`: the detail
shape below.

#### `GET /api/v1/pooled-funds/{id}/`
JWT. List shape plus the full transparent log:
```json
{ "...": "…list fields…", "total_disbursed": "3000.00",
  "contributions": [ { "id": 1, "contributor_user": 5, "contributor_name": "Moses Parent",
                       "amount": "5000.00", "deposit": 9, "deposit_reference": "SD-PF-…",
                       "created_at": "…" } ],
  "disbursements": [ { "id": 1, "amount": "3000.00", "destination": "school_settlement",
                       "description": "Bus hire deposit", "payout": null, "payout_status": null,
                       "disbursed_by": 2, "created_at": "…" } ] }
```
Only **confirmed** contributions appear in the log.

#### `POST /api/v1/pooled-funds/{id}/contribute/`
JWT, anyone who can see the fund. Body:
`{ amount, channel, payer_phone?, idempotency_key }`. Goes through the payments
collection flow (a `Deposit` with `purpose=pooled_fund_contribution`,
reference `SD-PF-…`). Response `201`/`200`: a Deposit (Section A shape).
When the webhook confirms it, the fund wallet is credited
(`entry_type=pooled_fund_contribution`), a contribution row appears, and the
contributor gets `pooled_fund_contribution_confirmed`.
Errors: `409 fund_not_open`, `409 fund_deadline_passed`.

#### `POST /api/v1/pooled-funds/{id}/close/`
JWT, **the fund's creator or a school_admin of that school** (or
platform_admin, which is audit-logged). Stops new contributions. Response `200`:
the detail shape. `409 fund_not_open` if the fund is already closed;
`403 forbidden` for other users who can see the fund.

#### `POST /api/v1/pooled-funds/{id}/disburse/`
JWT, **school_admin of that school only** (or platform_admin, audit-logged);
the creator cannot disburse unless they are that school's admin. Body:
```json
{ "amount": "3000", "destination": "school_settlement" | "external",
  "description": "Bus hire deposit", "phone_number": "0772…", "idempotency_key": "uuid" }
```
`description` is required. `school_settlement` moves the money into the
school settlement wallet (`entry_type=pooled_fund_disbursement`,
`reference_id=pooled:<fund>:<disbursement>`). `external` pays it out to
`phone_number` through an aggregator payout (`payout:<id>`); if the payout
fails, the money is reversed back into the fund. Disbursing is allowed while
the fund is open or closed. Once a **closed** fund's balance reaches 0, its
status becomes `disbursed`. Response `201`: the disbursement row.
Errors: `422 insufficient_funds` (more than the fund holds),
`400 description_required`, `403 forbidden`.

### Spending controls, savings, P2P, card freeze — Section C

#### Debit refusal codes (`authorize_debit`)
Every debit path (POS/merchant purchase, P2P, fee payment, savings move,
savings withdrawal) goes through `wallets.services.authorize_debit()`. A
refusal is `422` with
`{"code": "<first violation>", "detail": "<translated>", "violations": ["…all…"]}`.
Codes, in the order they are checked:
`wallet_not_spendable`, `card_frozen`, `card_lost`, `insufficient_funds`,
`per_transaction_cap_exceeded`, `daily_cap_exceeded`, `weekly_cap_exceeded`,
`category_blocked`, `category_not_allowed`, `item_blocked`, `merchant_blocked`
(purchases only), and `p2p_disabled`, `p2p_cap_exceeded` (P2P only).
Fee payments, savings moves and savings withdrawals are **exempt from
spending caps and category rules**; card-freeze and balance still apply.
"Today" and "this week" (Monday start) are Africa/Kampala. Daily/weekly spend
= the sum of `pos_purchase` debits on the student's main wallet.

#### `GET|POST /api/v1/product-categories/`, `GET|PATCH|PUT|DELETE /api/v1/product-categories/{id}/`
JWT. Read: anyone attached to the school (staff; parents of its students).
Write: that school's **school_admin** (platform_admin must pass `school`;
audit-logged). Fields: `{ id, school (read-only), name, is_unhealthy, active,
created_at, updated_at }`. `name` is unique per school. `?active=true|false`.

#### `GET|POST /api/v1/products/`, `GET|PATCH|PUT|DELETE /api/v1/products/{id}/`
Same permissions. Fields: `{ id, school, name, category, category_name,
price, active, created_at, updated_at }`. `category` must belong to the same
school (`400 category_invalid`). `?category=<id>`, `?active=`. (Section G adds
`merchant`.)

#### `GET|POST /api/v1/policies/`, `GET|PATCH|PUT|DELETE /api/v1/policies/{id}/`
JWT. One **school default** row per school (`student: null`, created
automatically) plus at most one **override** per student.
```json
{ "id": 4, "school": 1, "student": 12, "daily_spend_cap": "3000.00",
  "weekly_spend_cap": null, "per_transaction_cap": null, "p2p_daily_cap": "2000.00",
  "p2p_enabled": null, "low_balance_threshold": "1500.00",
  "blocked_categories": [2], "allowed_categories": [], "blocked_items": [7],
  "updated_by": 3, "created_at": "…", "updated_at": "…" }
```
`null` caps mean "no limit / inherit". `p2p_enabled: null` means inherit (a
school default of `null` means enabled). An empty `allowed_categories` means
every category is allowed.
- school_admin: reads all of their school's rows; PATCHes the default; CRUDs
  overrides in their school.
- parent: reads the default of their children's schools and the overrides of
  linked students; creates/PATCHes/DELETEs overrides for **linked students
  only**, and only to tighten: a cap above the school's, `p2p_enabled: true`
  when the school has it off, or allowing a category the school doesn't allow
  → `400 policy_cannot_loosen`.
- staff (canteen/merchant): read-only, own school.
- `POST` with `student: null` → `409 default_exists` (PATCH the default
  instead); a second override → `409 override_exists`. Referenced
  categories/items must be from the same school (`400 reference_invalid`).
  The default can't be deleted.

**Resolution** (`policies.services.get_effective_policy(student)`): caps =
the smaller of default and override; blocked categories/items/merchants =
union; allow-lists = intersection; P2P allowed only if both allow it;
`low_balance_threshold` = override, else default, else
`LOW_BALANCE_DEFAULT_THRESHOLD` (2000).

#### `GET /api/v1/students/{id}/effective-policy/`
JWT, anyone who can see the student. Response:
```json
{ "student": 12, "daily_spend_cap": "3000.00", "weekly_spend_cap": null,
  "per_transaction_cap": null, "p2p_daily_cap": "2000.00", "p2p_enabled": true,
  "low_balance_threshold": "1500.00", "blocked_category_ids": [2],
  "allowed_category_ids": null, "blocked_product_ids": [7],
  "blocked_merchant_ids": [], "allowed_merchant_ids": null }
```
`allowed_*_ids: null` = no allow-list. This is the same object the POS cache
embeds per card.

#### `POST /api/v1/wallets/{id}/savings/move-in/` and `/savings/move-out/`
JWT: guardians of the student, that school's school_admin, platform_admin.
`{id}` is the student's main **or** savings wallet. Body `{ "amount": "4000" }`.
move-in = main → savings, move-out = savings → main. Ledger (Part 1's
convention, kept): the debit side is always `savings_move_out` and the credit
side `savings_move_in`, with `reference_id=savings:<random>`. Response `200`:
`{ "main": {Wallet}, "savings": {Wallet} }`. `422` debit refusal codes apply.

#### `GET|PUT /api/v1/wallets/{id}/savings/withdrawal-window/`
GET: anyone allowed above. PUT: **guardians only**. Body
`{ "withdrawal_window_start": "2026-12-01T00:00:00Z", "withdrawal_window_end": "2027-01-31T00:00:00Z" }`
(both null = closed). Response `{ wallet, withdrawal_window_start,
withdrawal_window_end, is_open }`. `400 window_invalid` if only one is
given or end ≤ start.

#### `POST /api/v1/wallets/{id}/savings/withdraw/`
JWT, **guardians only** (`403` otherwise). Body
`{ "amount": "1000", "phone_number": "0772000111", "idempotency_key": "uuid" }`
(`phone_number` defaults to the guardian's). Allowed only while the window is
open (`409 withdrawal_window_closed`). Debits savings into clearing at once
(`entry_type=savings_withdrawal`, `reference_id=payout:<id>`) and starts a
mobile-money payout. Response `201`: a Payout
`{ id, school, purpose, source_wallet, amount, phone_number, description, status,
reference, aggregator_ref, failure_reason, created_at, completed_at }`.
`status: failed` means a `reversal` has already returned the money to
savings. Guardians get `savings_withdrawal_completed` / `_failed`.

#### `GET /api/v1/savings-goals/…` (Part 1 endpoint, extended)
Responses gain read-only `current_amount` (the savings wallet balance),
`progress_percent` (0–100, capped), `is_reached`, and `reached_at` (stamped
the first time savings reach the target, which also sends
`savings_goal_reached` to guardians). Several goals on one wallet each compare
against the whole savings balance.

#### `POST /api/v1/wallets/transfer/`
JWT, **a guardian of the sender**. Body:
```json
{ "sender_student": 12, "recipient_student": 15, "amount": "500", "note": "lunch" }
```
(or `recipient_card_uid` instead of `recipient_student`). Rules: same school
only (a student in another school is `404 recipient_not_found`); the sender
has an active card and no frozen card; the recipient's card is active
(`422 recipient_card_inactive`); P2P enabled for both (`422 p2p_disabled`);
within the sender's `p2p_daily_cap` (`422 p2p_cap_exceeded`); and
`authorize_debit` passes. Ledger: `p2p_transfer_out` / `p2p_transfer_in`,
`reference_id=p2p:<id>`. The recipient's guardians get
`p2p_transfer_received`. Response `201`:
```json
{ "id": 3, "school": 1, "sender_student": 12, "sender_name": "Amina Nakato",
  "recipient_student": 15, "recipient_name": "Brian Okello", "amount": "500.00",
  "note": "lunch", "initiated_by": 3, "device": null, "created_at": "…" }
```
The POS-device variant (card + PIN) is `POST /api/v1/pos/p2p-transfer/` (Section D).

#### `GET /api/v1/students/{id}/p2p-history/`
JWT, **guardians of the student and that school's school_admin only**
(other staff get `404`). Paginated transfers in either direction, same shape.

#### `GET /api/v1/p2p-alerts/`, `GET /api/v1/p2p-alerts/{id}/`, `POST /api/v1/p2p-alerts/{id}/review/`
JWT, **school_admin** (own school) / platform_admin. `?status=open|reviewed|dismissed`.
```json
{ "id": 1, "school": 1, "student": 15, "student_name": "Brian Okello",
  "rule": "many_distinct_senders", "details": {"distinct_senders": 4, "window_days": 7},
  "status": "open", "reviewed_by": null, "reviewed_at": null, "review_notes": "", "created_at": "…" }
```
Review body: `{ "status": "reviewed" | "dismissed", "review_notes": "…" }`.
When an alert is raised, the school's admins get `p2p_alert_raised`.

#### Cards (Part 1 endpoints, extended — same paths and response shape)
- `POST /api/v1/cards/{id}/freeze/` / `/unfreeze/`: now also notify the
  student's **other** guardians (`card_frozen` / `card_unfrozen`), and are
  audit-logged for platform_admin. A freeze blocks every debit through
  `authorize_debit` immediately and reaches offline POS devices on their next
  cache refresh (the card's `updated_at` changes). Unfreezing a **lost** card
  → `409 card_lost` (Part 1 would have silently reactivated it).
- **New** `POST /api/v1/cards/{id}/report-lost/`: guardian or school_admin
  (same rule as freeze). Sets `status: lost` permanently and notifies the other
  guardians (`card_reported_lost`). Replacement uses the Part 1
  `POST /api/v1/cards/{id}/reissue/` (school_admin).

### Canteen POS + offline sync (`pos` app) — Section D

**Device authentication.** Every device call sends
`Authorization: Device <raw device token>` (and optionally
`X-App-Version: 1.4.2`, stored on the device). The raw token is returned
**once**, at registration or rotation; the server stores only its SHA-256.
Unknown or revoked tokens → `401 {"detail": "Invalid or revoked device token."}`
immediately. A JWT is never accepted on device endpoints, and a device token
is never accepted on JWT endpoints. Every device call is a heartbeat
(`last_seen_at`, updated at most once a minute).

Device roles and allowed endpoints:

| Endpoint | canteen | merchant | attendance |
|---|---|---|---|
| `GET /pos/cache/`, `POST /pos/sync/`, `POST /pos/purchase/` | ✓ | ✓ | ✗ (403) |
| `POST /pos/p2p-transfer/` | ✓ | ✗ | ✗ |
| `POST /attendance/tap/` (Section F) | only if `attendance_on_canteen_devices` | ✗ | ✓ |

#### `GET|PATCH /api/v1/school-settings/`
JWT. Staff of a school read their own school's settings; **school_admin**
PATCHes them (platform_admin passes `?school=<id>`; audit-logged).
```json
{ "school": 1, "offline_spend_ceiling": "2000.00", "pin_lockout_threshold": 5,
  "device_stale_after_hours": 24, "attendance_notify_guardians": false,
  "attendance_on_canteen_devices": false, "updated_at": "…" }
```

#### `POST /api/v1/pos/devices/register/`
JWT, **school_admin** (platform_admin must add `"school": <id>`). Body:
`{ "device_name": "Canteen till 1", "device_role": "canteen" | "merchant" | "attendance", "merchant": <id, merchant devices only> }`.
Response `201` — the Device plus the one-time token:
```json
{ "id": 3, "school": 1, "merchant": null, "device_name": "Canteen till 1",
  "device_role": "canteen", "token_prefix": "q3X9aB1c", "status": "active",
  "last_seen_at": null, "last_sync_at": null, "app_version": "", "registered_by": 2,
  "created_at": "…", "revoked_at": null,
  "device_token": "q3X9aB1c…(43 chars) — SHOWN ONCE, store it on the device" }
```
Errors: `400 device_role_invalid`, `400 merchant_not_approved` (merchant
devices need a merchant approved by the school, Section G),
`400 merchant_not_allowed`.

#### `GET /api/v1/pos/devices/`, `GET /api/v1/pos/devices/{id}/`
JWT, school_admin (own school). Filters `?device_role=`, `?status=`.
`?stale=true` lists active devices that haven't synced for
`device_stale_after_hours` (never-synced devices count once they're older than that).

#### `POST /api/v1/pos/devices/{id}/revoke/`
JWT, school_admin. The token stops working on the next request. `200`: the Device.

#### `POST /api/v1/pos/devices/{id}/rotate-token/`
JWT, school_admin. Issues a new token (returned once as `device_token`); the
old one stops working. `409 device_revoked` for revoked devices.

#### `GET /api/v1/pos/cache/` — offline cache
Device (canteen/merchant). `?since=<ISO timestamp>` for an incremental
refresh; pass the previous response's `generated_at`. Response:
```json
{
  "generated_at": "2026-09-30T06:00:00.123456+00:00",
  "cache_version": 1790748000123,
  "since": null,
  "full": true,
  "full_school_ids": [1],
  "spend_day": "2026-09-30",
  "device": { "id": 3, "device_name": "Canteen till 1", "device_role": "canteen",
              "school_id": 1, "merchant_id": null },
  "school_ids": [1],
  "offline_spend_ceilings": { "1": "2000.00" },
  "pin_lockout_threshold": { "1": 5 },
  "pin_hash_scheme": {
    "format": "<algorithm>$<iterations>$<salt>$<hash>",
    "algorithm": "pbkdf2_sha256",
    "verify": "base64(PBKDF2-HMAC-SHA256(password=utf8(pin), salt=utf8(salt), iterations, dklen=32)) == hash",
    "note": "Django's default hasher; iterations are per-hash (read them from the string)."
  },
  "cards": [ {
    "card_id": 7, "card_uid": "04a2…", "status": "active",
    "pin_hash": "pbkdf2_sha256$870000$Zp1…$k3N…=",
    "student_id": 12, "student_display_name": "Amina Nakato", "photo_url": null,
    "school_id": 1, "wallet_id": 31, "balance": "14500.00", "today_spend": "3000.00",
    "offline_spend_ceiling": "2000.00",
    "policy": { "daily_spend_cap": "5000.00", "weekly_spend_cap": null,
                "per_transaction_cap": null, "p2p_daily_cap": null, "p2p_enabled": true,
                "low_balance_threshold": "2000.00", "blocked_category_ids": [2],
                "allowed_category_ids": null, "blocked_product_ids": [7],
                "blocked_merchant_ids": [], "allowed_merchant_ids": null }
  } ],
  "products": [ { "id": 5, "name": "Rice & beans", "category_id": 1, "category_name": "Meals",
                  "price": "3000.00", "active": true, "school_id": 1, "merchant_id": null } ],
  "categories": [ { "id": 1, "name": "Meals", "is_unhealthy": false, "active": true, "school_id": 1 } ]
}
```
**PIN verification offline (exact scheme).** `pin_hash` is Django's
`make_password(pin)` output: `pbkdf2_sha256$<iterations>$<salt>$<b64hash>`.
To verify an entered PIN: split on `$`, compute
`PBKDF2-HMAC-SHA256(password = pin as UTF-8 bytes, salt = salt as UTF-8 bytes, iterations = int(iterations), dkLen = 32)`,
base64-encode it (standard alphabet, with padding) and compare it, in constant
time, to `<b64hash>`. Iterations are 870,000 today (Django 5.1) and may
change per hash, so always read them from the string. Any other `algorithm`
prefix means "can't verify offline": treat the card as online-only. The
device must count wrong PINs locally, refuse the card after
`pin_lockout_threshold` wrong attempts, and report them on the next sync.

**Incremental refresh rules.** With `since`, `cards` contains only cards
whose card, student, main wallet (any ledger movement) or policy override
changed after `since`, and `products`/`categories` only rows changed after
`since`. If a school's **default policy or settings** changed, every card
of that school is re-sent and the school is listed in `full_school_ids`.
Cards are never deleted from the response: a retired card arrives with
`status: "lost"`. Replace cached rows by `card_uid` / `id`.
`today_spend` is for `spend_day` (Africa/Kampala); the device resets its own
counters at local midnight.

**What the device must enforce offline** (the server re-checks everything
on sync): card `status == active`; PIN; the item/category/merchant rules in
`policy`; `per_transaction_cap`; `daily_spend_cap` against
`today_spend + offline spend since the refresh`; and never let
`balance − offline spend` go below `−offline_spend_ceiling` (the ceiling is
how far a card may go below its cached balance, across all devices).

#### `POST /api/v1/pos/sync/` — batch sync
Device (canteen/merchant). Body:
```json
{ "transactions": [ {
    "idempotency_key": "b1f0c7e2-…",           // UUID generated on the device, per sale
    "card_uid": "04a2…",
    "amount": "4500.00",
    "items": [ { "product_id": 5, "quantity": 1, "unit_price": "3000.00" },
               { "description": "Mandazi", "category_id": 3, "quantity": 3, "unit_price": "500.00" } ],
    "device_local_timestamp": "2026-09-30T09:15:02+03:00",
    "pin_verified": true
  } ],
  "pin_failures": [ { "card_uid": "04a2…", "failed_attempts": 2,
                      "device_local_timestamp": "2026-09-30T09:14:40+03:00" } ] }
```
At most 500 transactions per call. `items` is optional, but when present the
line totals (`quantity × unit_price`) must add up to `amount` exactly.
`product_id` must belong to the device's scope; `category_id` is used only
when there's no product.
Response `200`, **always**, even if every transaction was rejected:
```json
{ "results": [ { "idempotency_key": "b1f0…", "status": "applied", "transaction_id": 88,
                 "amount": "4500.00", "applied_amount": "4500.00", "shortfall_amount": "0.00",
                 "flags": [], "reason": null } ],
  "balances": [ { "card_uid": "04a2…", "card_status": "active", "wallet_id": 31,
                  "balance": "10000.00", "today_spend": "7500.00" } ],
  "server_time": "…" }
```
Processing: transactions are applied in `device_local_timestamp` order. Each
one is independent (one bad transaction never fails the batch).
`results[].status`:
- `applied` — fully debited (`reference_id=pos:<transaction_id>`).
- `shortfall` — the sale happened offline but the wallet didn't hold enough:
  the wallet was debited to 0 (`applied_amount`), and `shortfall_amount`
  is sent to admin review. The sale is **recorded, never dropped**.
- `rejected` — nothing recorded against a wallet; `reason` ∈
  `idempotency_key_required, unknown_card (not in the device's scope),
  amount_invalid, amount_too_large, timestamp_required, items_invalid,
  unknown_product, amount_mismatch, malformed, internal_error`.
  Rejections are stored (so a replay returns `duplicate`), except ones
  without an idempotency key.
- `duplicate` — this `(device, idempotency_key)` was already processed; the
  original result is returned and no money moves.

`flags` lists the rules an offline sale broke even though it was recorded:
`card_frozen, card_lost, per_transaction_cap_exceeded, daily_cap_exceeded,
weekly_cap_exceeded, category_blocked, category_not_allowed, item_blocked,
merchant_blocked, exceeds_offline_ceiling` (shortfall larger than the
school's ceiling). A flagged or short transaction goes to the review queue,
and the school's admins get `shortfall_flagged` / `pos_transaction_flagged`.
`pin_failures` add up per card over 24 h; reaching the school's
`pin_lockout_threshold` freezes the card (guardians get
`card_locked_pin_failures`). `balances` covers every card in the batch:
**overwrite the cached balance with it.**

#### `POST /api/v1/pos/purchase/` — online sale
Device (canteen/merchant). Same fields as one sync transaction, plus an
optional `"pin": "1234"`, which the server verifies (`422 pin_invalid`, and
it counts towards lockout). `authorize_debit()` is enforced in real time: a
refused sale → `422 {"code": "<refusal code>", "detail": …, "violations": [...]}`
and **nothing is recorded**. Success `201` (replay `200` with
`status: "duplicate"`): the sync result object plus `"balance": {card balance row}`.
A validation rejection (e.g. `unknown_card`) → `422` with the result and
`code = reason`.

#### `POST /api/v1/pos/p2p-transfer/`
Device (**canteen** only; online only). The sender presents their card and PIN.
```json
{ "idempotency_key": "uuid", "sender_card_uid": "04a2…", "pin": "1234",
  "recipient_card_uid": "04b7…", "amount": "500", "note": "" }
```
Both cards must be in the device's school (`404 unknown_card`). Wrong PIN →
`422 pin_invalid` (counts towards lockout). All Section C P2P rules and
codes apply. `201`: the P2PTransfer (Section C shape, `device` set); a replay
with the same key returns the same transfer.

#### `GET /api/v1/pos/transactions/`, `GET /api/v1/pos/transactions/{id}/`
JWT, school_admin (own school). Every POS sale. Filters `?device=`,
`?student=`, `?sync_status=`, `?review_status=`.
```json
{ "id": 88, "device": 3, "device_name": "Canteen till 1", "school": 1, "merchant": null,
  "card": 7, "card_uid": "04a2…", "student": 12, "student_name": "Amina Nakato", "wallet": 31,
  "channel": "offline_sync", "amount": "4500.00", "applied_amount": "3000.00",
  "shortfall_amount": "1500.00", "recovered_amount": "0.00", "outstanding_amount": "1500.00",
  "idempotency_key": "b1f0…", "device_local_timestamp": "…", "received_at": "…",
  "sync_status": "shortfall", "reject_reason": "", "flags": ["item_blocked"],
  "pin_verified": true, "ledger_reference": "pos:88", "review_status": "pending",
  "resolution": "", "reviewed_by": null, "reviewed_at": null, "review_notes": "",
  "items": [ { "id": 1, "product": 5, "description": "Rice & beans", "category": 1,
               "quantity": 1, "unit_price": "3000.00", "line_total": "3000.00" } ] }
```
`review_status` ∈ `none, pending, recovery_pending, resolved`;
`resolution` ∈ `accept, write_off, recover_from_next_topup, charge_guardian`.

#### `GET /api/v1/pos/shortfalls/`, `GET /api/v1/pos/shortfalls/{id}/`
JWT, school_admin. The review queue: by default `review_status=pending`
(shortfalls **and** flagged sales). `?type=shortfall|flagged`,
`?review_status=recovery_pending|resolved` to see the others. Same shape.

#### `POST /api/v1/pos/shortfalls/{id}/resolve/`
JWT, school_admin. Body `{ "resolution": "...", "review_notes": "…" }`.

| resolution | allowed when | ledger effect |
|---|---|---|
| `accept` | flagged, no shortfall | none (acknowledged) |
| `write_off` | shortfall > 0 | none: the school/merchant absorbs the loss; the missing money never existed in any wallet |
| `recover_from_next_topup` | shortfall > 0 | collects immediately from the current balance, then from every later **confirmed deposit** into the main wallet until repaid: main → the sale's settlement wallet, `entry_type=shortfall_recovery`, `reference_id=recovery:<txn>:<n>`. Status `recovery_pending` → `resolved` |
| `charge_guardian` | shortfall > 0 | as above, plus a collection request (`Deposit`, `idempotency_key=shortfall:<txn>`) for the outstanding amount to the primary guardian's phone; when paid, recovery completes |

Errors: `409 not_pending`, `400 resolution_invalid`.

### Fee top-ups (`fees` app) — Section E

#### `GET|POST /api/v1/fee-categories/`, `GET|PATCH|PUT|DELETE /api/v1/fee-categories/{id}/`
JWT. Read: the school's staff and guardians of its students. Write: that
school's **school_admin** (platform_admin passes `school`; audit-logged).
```json
{ "id": 2, "school": 1, "name": "Exam fee", "amount_type": "fixed",
  "fixed_amount": "6000.00", "min_amount": null, "max_amount": null, "active": true,
  "due_date": "2026-11-15", "applicable_classes": ["P4", "P5"],
  "created_at": "…", "updated_at": "…" }
```
`amount_type: fixed` needs `fixed_amount`; `range` needs
`0 < min_amount ≤ max_amount` (`400 fee_amount_invalid`). An empty
`applicable_classes` means every class. Filters: `?active=true|false`,
`?class_name=P4` (fees that apply to that class).

#### `POST /api/v1/fees/pay/`
JWT, **a guardian of the student or that school's school_admin**. Pays from
the student's **main** wallet into the school settlement wallet
(`entry_type=fee_payment`, `reference_id=fee:<id>`).
```json
{ "student": 12, "fee_category": 2, "amount": "6000", "idempotency_key": "uuid" }
```
`amount` may be omitted for a fixed fee (and must equal it if given).
Goes through `authorize_debit` with kind `fee_payment`: **card freeze and
balance apply; daily/weekly/per-transaction caps and category rules do not.**
Response `201` (`200` on idempotent replay):
```json
{ "id": 5, "school": 1, "student": 12, "student_name": "Amina Nakato", "fee_category": 2,
  "fee_category_name": "Exam fee", "amount": "6000.00", "paid_by": 3,
  "ledger_reference": "fee:5", "status": "completed", "idempotency_key": "uuid", "created_at": "…" }
```
Errors: `404 not_found` (not your student / other school's category),
`409 fee_inactive`, `400 fee_not_applicable`, `400 fee_amount_invalid`,
`422 insufficient_funds | card_frozen`, `409 idempotency_conflict`.

#### `GET /api/v1/fees/payments/`, `GET /api/v1/fees/payments/{id}/`
JWT. Guardians: their students' payments; school_admin: their school's.
Filters `?student=<id>` and `?fee_category=<id>` give the history per student
and per category. Paginated, same shape as above.

### Attendance tap-in (`attendance` app) — Section F

#### `POST /api/v1/attendance/tap/`
**Device** auth. Allowed: `attendance` devices, and `canteen` devices only if
the school has `attendance_on_canteen_devices = true` (otherwise `403`).
No money moves. Body is either **one tap**:
```json
{ "idempotency_key": "uuid", "card_uid": "04a2…", "direction": "in",
  "device_local_timestamp": "2026-09-30T07:30:00+03:00" }
```
or an **offline queue**: `{ "taps": [ {tap}, {tap}, … ] }` (≤ 500).
`direction` ∈ `in | out` (default `in`). Response `200`:
```json
{ "results": [ { "idempotency_key": "uuid", "status": "created", "record_id": 41,
                 "student_id": 12, "direction": "in", "reason": null } ],
  "created": 1 }
```
`status`: `created`; `duplicate` (same device + key already recorded; the
original record is returned); `rejected` with `reason` ∈
`idempotency_key_required, unknown_card (not a card of the device's own school),
direction_invalid, timestamp_required, malformed`.
Naive timestamps are read as Africa/Kampala. If the school enabled
`attendance_notify_guardians`, a student's **first `in` tap of the day**
(Kampala) notifies their guardians (`attendance_tap_in`).

#### `GET /api/v1/attendance/`
JWT. school_admin: their school; parents: their own children only; others:
empty. Filters: `?date=YYYY-MM-DD` (a Kampala day), or `?from=` / `?to=`
(inclusive Kampala days), `?student=`, `?direction=`. Paginated:
```json
{ "id": 41, "school": 1, "student": 12, "student_name": "Amina Nakato", "card": 7,
  "device": 5, "device_name": "Main gate", "direction": "in",
  "device_local_timestamp": "2026-09-30T04:30:00Z", "received_at": "…", "idempotency_key": "uuid" }
```

#### `GET /api/v1/students/{id}/attendance/`
JWT, **guardians of the student and that school's school_admin**. Same
filters and shape.

### Approved nearby merchant network (`merchants` app) — Section G

A merchant can charge a school's cards only while **both** its platform
`status` is `approved` **and** that school's approval is `approved`.

#### `GET|POST /api/v1/merchants/`, `GET|PATCH /api/v1/merchants/{id}/`
JWT. List visibility: school_admin sees every merchant (so a school can find
and approve a merchant that a neighbouring school registered); parents see
merchants approved for their children's schools (so they can block them);
merchant_staff see their own merchant; platform_admin sees all.
```json
{ "id": 3, "name": "Ntinda Bookshop", "category": "bookshop", "contact_phone": "0772…",
  "status": "approved", "approved_school_ids": [1],
  "my_school_approval": "approved", "created_at": "…", "updated_at": "…" }
```
`approved_school_ids` only lists schools the caller belongs to (merchant_staff
and platform_admin see all of them). `my_school_approval` is the caller's own
school's approval status (`pending | approved | suspended | null`).
Create: **school_admin** (the merchant is immediately approved for their
school) or platform_admin (unattached). PATCH: the admin who registered it,
or platform_admin (who may also set `status`, the platform-wide switch).

#### `POST /api/v1/merchants/{id}/approve/`, `POST /api/v1/merchants/{id}/suspend/`
JWT, **school_admin — for their own school only** (platform_admin passes
`"school": <id>`; audit-logged). Response
`{ "merchant": 3, "school": 1, "status": "approved", "decided_at": "…" }`.
Approving creates the merchant's settlement wallet for that school.
Suspending removes the school's cards from the merchant's devices at their
next cache refresh; sales synced afterwards are rejected `unknown_card`.

#### `POST /api/v1/merchants/{id}/staff/`
JWT, platform_admin or a school_admin of an approving school. Body
`{ "user": <id of a merchant_staff user> }`. Links the user to the merchant.

#### `GET /api/v1/merchants/{id}/statement/`
JWT. **merchant_staff of this merchant**: all of its schools (`?school=` to
narrow). **school_admin**: their own school only. `?from=` / `?to=`
(inclusive Kampala days). Response:
```json
{ "merchant": 3, "school_ids": [1, 2],
  "balances": [ { "school_id": 1, "wallet_id": 77, "balance": "1200.00" } ],
  "total_credits": "1700.00", "total_debits": "0.00",
  "entries": { "count": 2, "next": null, "previous": null,
               "results": [ {LedgerEntry: id, wallet, amount, direction, entry_type, reference_id, description, created_at} ] } }
```

#### Merchant devices
They are ordinary `Device`s with `device_role: merchant` and a `merchant`,
registered by a school_admin of an approving school
(`POST /pos/devices/register/` with `"merchant": <id>`). They use the **same**
`/pos/cache/`, `/pos/sync/` and `/pos/purchase/` endpoints (not
`/pos/p2p-transfer/`). Differences:
- the cache contains the cards of **every school that approved the
  merchant**, and only the merchant's own products (`Product.merchant`);
- sales credit the merchant's settlement wallet **for the card holder's
  school**; `PosTransaction.merchant` is set;
- the `merchant_blocked` rule applies (parents block via policy).

#### Changes to Section C endpoints
- `Product` gains `merchant` (null = canteen). It must be a merchant
  approved for the school (`400 merchant_not_approved`). `/products/?merchant=<id>`.
- `Policy` gains `blocked_merchants` and `allowed_merchants` (id lists;
  an empty allow-list = every approved merchant). Referenced merchants must
  be approved for the school (`400 reference_invalid`). A parent's override
  may block merchants for their child; resolution unions blocks and
  intersects allow-lists.

### Disputes & refunds (`disputes` app) — Section H

#### `POST /api/v1/disputes/`
JWT, **a guardian of the student** (students later). Exactly one target:
```json
{ "pos_transaction": 88, "reason_category": "wrong_amount", "description": "Only bought one samosa" }
```
or `{ "ledger_entry": 512, … }` for a **fee payment or shortfall recovery**
debit. Canteen and merchant sales are disputed via their `pos_transaction`.
`reason_category` ∈ `wrong_amount, not_received, unauthorized, duplicate, other`.
Response `201`:
```json
{ "id": 4, "school": 1, "raised_by": 3, "student": 12, "student_name": "Amina Nakato",
  "pos_transaction": 88, "ledger_entry": null, "reason_category": "wrong_amount",
  "description": "…", "status": "open", "resolution_notes": "", "refund_amount": "0.00",
  "original_amount": "3000.00", "refunded_total": "0.00",
  "resolved_by": null, "resolved_at": null, "created_at": "…", "updated_at": "…" }
```
`original_amount` = what was actually debited (for POS: applied + recovered).
`refunded_total` = the sum of all refunds already granted on this
transaction, across disputes. Errors: `404` (not your child's transaction),
`409 dispute_already_open` (one open dispute per transaction, DB-enforced),
`400 not_disputable` (credits, P2P, deposits, rejected sales),
`400 target_required`.

#### `GET /api/v1/disputes/`, `GET /api/v1/disputes/{id}/`
JWT. school_admin: their school's queue; guardians: disputes they raised or
that concern their children. Filters `?status=`, `?student=`.

#### `POST /api/v1/disputes/{id}/review/`
JWT, **school_admin of that school**. `open → under_review`. `409 dispute_not_open`.

#### `POST /api/v1/disputes/{id}/resolve/`
JWT, **school_admin of that school only**: not platform_admin (`403`),
not canteen/merchant staff. From `open` or `under_review`.
```json
{ "outcome": "refund", "refund_amount": "1000", "resolution_notes": "Overcharged" }
{ "outcome": "deny", "resolution_notes": "CCTV confirms purchase" }
```
A refund credits the student's **main** wallet from the wallet that received
the money (school settlement, or the merchant's settlement wallet for that
school): `entry_type=refund`, `reference_id=refund:<dispute id>`. Partial
refunds are allowed; **the sum of refunds on one transaction can never
exceed `original_amount`** (`422 refund_exceeds_original`, enforced under a
row lock). `422 refund_source_insufficient` if the receiving wallet no longer
holds the money. The raiser is notified on every status change
(`dispute_status_changed`).

### Notifications (`notifications` app) — Section I

Every notification is rendered **once, in the recipient's
`preferred_language`** (en / lg / sw), and stored as a `NotificationEvent` per
channel. `in_app` is always delivered (it *is* the in-app notification).
`sms` and `push` are dispatched by Celery after the money movement commits.
In Part 2 they are **stub backends that log** what they would send (`status: logged`).

**Event types** (`event_type`) and their `payload` keys (all ids are ints;
amounts are pre-formatted strings such as `"5,000"`):

| event_type | recipient | payload keys |
|---|---|---|
| `deposit_confirmed` | parent who paid | deposit_id, amount, student_id, student_name |
| `deposit_failed` | parent who paid | deposit_id, amount, student_id, student_name, reason |
| `contributor_topup_received` | all guardians | + contributor_name |
| `gift_received` | all guardians | + gift_voucher_id, sender_name, message |
| `recurring_topup_executed` / `_failed` / `_paused` | the parent | + recurring_topup_id (+ reason / failures) |
| `low_balance` | each guardian | student_id, student_name, wallet_id, balance, threshold, **action** |
| `savings_goal_reached` | all guardians | student_id, student_name, goal_id, goal_name, target_amount |
| `savings_withdrawal_completed` / `_failed` | all guardians | payout_id, amount, student_id, student_name, phone_number, reason |
| `card_frozen` / `card_unfrozen` / `card_reported_lost` | the **other** guardians | card_id, student_id, student_name, actor_name |
| `card_locked_pin_failures` | all guardians | card_id, student_id, student_name, failures |
| `p2p_transfer_received` | recipient's guardians | student_id, student_name, sender_name, amount, p2p_transfer_id |
| `p2p_alert_raised` | school admins | alert_id, student_id, student_name, rule |
| `shortfall_flagged` / `pos_transaction_flagged` | school admins | pos_transaction_id, student_id, student_name, device_name, shortfall_amount, flags |
| `dispute_status_changed` | the raiser | dispute_id, status, student_id, refund_amount, notes |
| `attendance_tap_in` | all guardians (opt-in per school) | student_id, student_name, time, attendance_record_id |
| `pooled_fund_contribution_confirmed` | the contributor | fund_id, fund_title, amount |
| `data_request_updated` | the requester | request_id, request_type, status |

**Low-balance one-tap top-up**: `payload.action` =
`{ "type": "top_up", "student_id": 12, "wallet_id": 31, "suggested_amount": "5000" }`.
The parent app can pass `wallet_id` and `suggested_amount` straight to
`POST /payments/deposits/`. A low-balance alert fires when a debit takes the
student's **main** wallet from ≥ threshold to < threshold. The threshold is
the guardian's own per-student setting, else the effective policy's
`low_balance_threshold`, else 2,000. It fires at most once per guardian per
wallet every `LOW_BALANCE_ALERT_THROTTLE_HOURS` (12), de-duplicated in Redis.

#### `GET /api/v1/notifications/`, `GET /api/v1/notifications/{id}/`
JWT, the caller's own **in-app** notifications (newest first). `?unread=true`,
`?event_type=`. The paginated response adds `unread_count`:
```json
{ "count": 3, "next": null, "previous": null, "unread_count": 2,
  "results": [ { "id": 51, "event_type": "low_balance", "title": "Low balance",
                 "body": "Amina Nakato's balance is 1,500 UGX, below your alert level of 2,000 UGX. Tap to top up.",
                 "payload": {…}, "channel": "in_app", "status": "sent",
                 "created_at": "…", "sent_at": "…", "read_at": null } ] }
```

#### `POST /api/v1/notifications/{id}/read/`
JWT. Marks it read (idempotent). `200`: the notification. Someone else's → `404`.

#### `POST /api/v1/notifications/read-all/`
JWT. `200 {"marked_read": 2}`.

#### `GET|PUT|PATCH /api/v1/notifications/preferences/`
JWT.
```json
{ "in_app_enabled": true, "sms_enabled": false, "push_enabled": true,
  "low_balance_thresholds": { "12": "2500.00" }, "updated_at": "…" }
```
`low_balance_thresholds` keys must be the caller's linked students (`400` otherwise).

#### `GET|POST /api/v1/notifications/push-tokens/`, `DELETE /api/v1/notifications/push-tokens/{token}/`
JWT. `POST {"token": "<FCM/APNs token>", "platform": "android" | "ios" | "web"}`
is an upsert: `201` when new, `200` when the token already existed (it is
moved to the caller, e.g. a phone that changed hands). Call `DELETE` on logout.

### Privacy dashboard support (`privacy` app) — Section J

#### `GET /api/v1/privacy/my-data/` (`?format=json` default, `?format=csv`)
JWT, **parents only** (`403` otherwise). JSON:
```json
{ "generated_at": "…",
  "profile": { "id": 3, "email": "…", "full_name": "…", "phone_number": "…", "role": "parent",
               "preferred_language": "en", "date_joined": "…" },
  "guardian_verification": { "status": "verified", "full_name": "…", "id_document_type": "national_id",
                             "id_number": "…", "verified_at": "…" },
  "students": [ { "id": 12, "name": "Amina Nakato", "class_name": "P4", "date_of_birth": null,
                  "photo_url": null, "school": { "id": 1, "name": "…" }, "relationship": "mother",
                  "cards": [ { "card_uid": "04a2…", "status": "active", "biometric_enrolled": false, "issued_at": "…" } ],
                  "wallets": [ { "id": 31, "wallet_type": "main", "balance": "14500.00",
                                 "ledger": [ { "id": 9, "created_at": "…", "direction": "credit", "amount": "20000.00",
                                               "entry_type": "deposit", "reference_id": "deposit:4", "description": "…" } ] } ] } ] }
```
Only the caller's own linked students are included. **`pin_hash` is never
included**, and neither are system wallets. `?format=csv` downloads
`schooldimes-my-data.csv` (`Content-Disposition: attachment`) with columns
`section, student, field_or_date, value_or_direction, amount, entry_type, reference_id, description`.

#### `GET|POST /api/v1/privacy/data-requests/`, `GET /api/v1/privacy/data-requests/{id}/`
JWT. Create: **parents**. List: the requester sees their own; school_admin
sees requests about their school's students, or from parents of them.
```json
{ "request_type": "export" | "correction" | "deletion", "subject": "self" | "student",
  "student": 12, "details": "Date of birth is wrong" }
```
`student` is required when `subject=student` and must be a linked child
(`404`). Response `201`:
```json
{ "id": 2, "requested_by": 3, "request_type": "deletion", "subject": "student", "student": 12,
  "school": 1, "details": "…", "status": "pending", "notes": "", "handled_by": null,
  "handled_at": null, "created_at": "…",
  "retention_notice": "Your personal details have been removed … Financial records (the ledger …) are kept …" }
```
`retention_notice` is set on every **deletion** request (null otherwise), so
the parent sees up front what will be kept.

#### `POST /api/v1/privacy/data-requests/{id}/handle/`
JWT, **school_admin** (of a school the request concerns). Body
`{ "status": "in_progress" | "completed" | "rejected", "notes": "…" }`.
Completing a **deletion** performs an irreversible redaction and appends the
retention notice to `notes`:
- `subject=student`: name → "Redacted student <id>", class/date of
  birth/photo cleared, cards marked `lost`, recurring top-ups stopped,
  top-up links revoked. Refused with `409 balance_not_zero` while the child's
  wallets hold money (withdraw or spend it first).
- `subject=self`: email → `redacted-<id>@redacted.invalid`, name/phone
  cleared, account deactivated with an unusable password, KYC name/ID
  number redacted, push tokens and in-app notifications deleted, schedules
  and links stopped. Children for whom this parent is the **only** guardian
  are redacted as above.
- **Ledger entries, deposits, POS sales, fee payments and disputes are never
  deleted.**

Other transitions notify the requester (`data_request_updated`). Closed
requests → `409 request_closed`. Export and correction requests are tracked
here; the export itself is `/privacy/my-data/`, and corrections are made by
the admin through the normal endpoints.

### Analytics & reconciliation (`analytics` app) — Section K

Read-only, computed on request from existing rows (nothing extra stored).
**Scope**: school_admin gets their own school. platform_admin passes
`?school=<id>`, or omits it for a **cross-school summary** (sales-summary adds
`by_school`; reconciliation returns `{"date", "schools": [...]}`). Everyone
else gets `403`. Date filters `?from=YYYY-MM-DD&to=YYYY-MM-DD` are inclusive
Africa/Kampala days (default: the last 30 days, max 366). Sales are bucketed by
the sale's `device_local_timestamp`. **gross** = amount rung up;
**collected** = amount the ledger actually moved (the difference is
shortfall). Rejected POS transactions are excluded everywhere.

#### `GET /api/v1/analytics/sales-summary/`
```json
{ "from": "2026-09-01", "to": "2026-09-30",
  "totals": { "transactions": 3, "gross_amount": "7000.00", "collected_amount": "7000.00", "shortfall_amount": "0.00" },
  "by_day": [ { "date": "2026-09-15", "transactions": 2, "gross_amount": "…", "collected_amount": "…" } ],
  "by_device": [ { "device_id": 3, "device_name": "Till 1", "transactions": …, "gross_amount": …, "collected_amount": … } ],
  "by_merchant": [ { "merchant_id": null, "merchant_name": "School canteen", … } ],
  "by_school": [ { "school_id": 1, "school_name": "…", … } ] }
```
(`by_school` appears only in platform_admin's cross-school view.)

#### `GET /api/v1/analytics/best-sellers/?limit=10`
From `PosTransactionItem`, ordered by quantity:
`{ from, to, results: [ { product_id, name, quantity, revenue, transactions } ] }`.

#### `GET /api/v1/analytics/peak-hours/`
All 24 Kampala hours: `{ from, to, timezone, results: [ { hour: 0..23, transactions, gross_amount } ] }`.

#### `GET /api/v1/analytics/category-breakdown/`
```json
{ "from": "…", "to": "…", "total_item_revenue": "7000.00", "unhealthy_revenue": "4000.00",
  "unhealthy_share_percent": 57.1,
  "results": [ { "category_id": 2, "name": "Sugary drinks", "is_unhealthy": true, "quantity": 4,
                 "revenue": "4000.00", "share_percent": 57.1 } ] }
```
The nutrition flag is the share of item revenue in categories the school
marks `is_unhealthy`.

#### `GET /api/v1/analytics/students/{id}/spending/`
JWT, **that school's school_admin and the student's guardians only**
(platform_admin and everyone else: `404`). From the student's ledger
(bucketed by entry `created_at`) and POS items:
`{ student, from, to, purchases_total, fees_total, p2p_sent_total,
p2p_received_total, topups_total, refunds_total, by_day: [{date, spent}],
by_category: [{name, is_unhealthy, quantity, revenue}], top_items: [{name, quantity, revenue}] }`.

#### `GET /api/v1/analytics/reconciliation/?date=YYYY-MM-DD`
One Kampala day (default today). POS figures are for transactions
**received (synced)** that day, which is when their ledger entries were
written.
```json
{ "school": 1, "date": "2026-09-30", "timezone": "Africa/Kampala",
  "devices": [ { "device_id": 3, "device_name": "Till 1", "device_role": "canteen", "status": "active",
                 "last_sync_at": "…", "transactions": 3, "rejected": 0,
                 "collected_amount": "7000.00", "ledger_amount": "7000.00", "matches": true } ],
  "stale_devices": [ { "device_id": 5, "device_name": "…", "last_sync_at": null } ],
  "unresolved_reviews": { "count": 1, "outstanding_shortfall": "2000.00" },
  "deposits": { "confirmed_count": 4, "confirmed_amount": "…", "ledger_amount": "…", "matches": true,
                "pending_count": 1, "pending_amount": "…" },
  "fee_payments": { "count": 2, "amount": "…", "ledger_amount": "…", "matches": true },
  "pooled_funds": [ { "fund_id": 3, "title": "…", "status": "open", "balance": "…" } ],
  "system_wallets": { "school_settlement": "…", "aggregator_clearing": "-…" },
  "books_total": "0.00", "books_balanced": true }
```
Every `*_amount` next to a `ledger_amount` is recomputed from the
`LedgerEntry` rows carrying its `reference_id` (`pos:`, `deposit:`,
`fee:`), and `matches` shows whether they agree. `books_total` is the sum of
every wallet in the school, which double-entry keeps at exactly 0.

### Developer tools (not endpoints) — Section M
`manage.py simulate_pos [--base-url URL]`, `manage.py mock_webhook <reference> [--fail] [--reason R] [--list] [--base-url URL]`,
`manage.py run_recurring_topups [--now]`, `manage.py build_locale`. See
`docs/TESTING_WITHOUT_DEVICES.md`. Every endpoint above has a runnable
example in `docs/requests/*.http`.

### Part 1 endpoints affected by Part 2 (read this if you built against Part 1)
Every change below is **additive**. No Part 1 field was renamed or removed.
- `GET /api/v1/wallets/` (school staff): now also lists the school's
  **system wallets** (`wallet_type` ∈ `school_settlement, aggregator_clearing,
  pooled_fund, merchant_settlement`) with `student: null`. Parents only ever
  see their children's `main`/`savings` wallets. `aggregator_clearing` is
  normally **negative** (see the chart of wallets). Clients showing student
  balances should filter to `wallet_type in (main, savings)`.
- `POST /api/v1/students/` now also creates the student's `main` and
  `savings` wallets.
- `LedgerEntry.entry_type` gains `reversal` and `shortfall_recovery`. Part 2
  entries carry `reference_id="<kind>:<id>"`.
- `GET /api/v1/savings-goals/…` gains `current_amount`, `progress_percent`,
  `is_reached`, `reached_at` (read-only).
- `POST /api/v1/cards/{id}/freeze/` and `/unfreeze/` also notify the other
  guardians. Unfreezing a **lost** card now returns `409 card_lost`. New:
  `POST /api/v1/cards/{id}/report-lost/`.
- `School.policy_defaults` (in `/api/v1/schools/`) is **superseded** by
  `/api/v1/policies/`. It is still returned and writable, but ignored.
- New Part 2 student sub-routes: `/students/{id}/effective-policy/`,
  `/students/{id}/p2p-history/`, `/students/{id}/attendance/`.
- Known Part 1 quirk, **not changed**: `GET /api/v1/students/{id}/` returns
  `403` for parents (their `school` is null and `IsSameSchoolObject` refuses).
  The list endpoint works. See DECISIONS.md; a one-line fix is waiting for approval.

### Part 2 endpoint index
| Area | Endpoints |
|---|---|
| Payments | `payments/deposits/`, `payments/topup-links/`, `payments/gift-vouchers/`, `payments/recurring-topups/`, `payments/webhook/`, `public/topup-links/{token}/…` |
| Pooled funds | `pooled-funds/`, `…/{id}/contribute|close|disburse/` |
| Policy & catalogue | `policies/`, `product-categories/`, `products/`, `students/{id}/effective-policy/` |
| Wallet ops | `wallets/{id}/savings/move-in|move-out|withdraw|withdrawal-window/`, `wallets/transfer/`, `students/{id}/p2p-history/`, `p2p-alerts/`, `cards/{id}/report-lost/` |
| POS | `school-settings/`, `pos/devices/…`, `pos/cache/`, `pos/sync/`, `pos/purchase/`, `pos/p2p-transfer/`, `pos/transactions/`, `pos/shortfalls/…` |
| Fees | `fee-categories/`, `fees/pay/`, `fees/payments/` |
| Attendance | `attendance/tap/`, `attendance/`, `students/{id}/attendance/` |
| Merchants | `merchants/`, `…/{id}/approve|suspend|staff|statement/` |
| Disputes | `disputes/`, `…/{id}/review|resolve/` |
| Notifications | `notifications/`, `…/{id}/read/`, `…/read-all/`, `…/preferences/`, `…/push-tokens/` |
| Privacy | `privacy/my-data/`, `privacy/data-requests/`, `…/{id}/handle/` |
| Analytics | `analytics/sales-summary|best-sellers|peak-hours|category-breakdown|reconciliation/`, `analytics/students/{id}/spending/` |

---

## Part 4A — Web surfaces & parent-app readiness

Every Part 4A addition is **additive**: no existing path, field or response
shape changed (the one behaviour fix is called out explicitly). Same
conventions as Part 2 (trailing slash optional on new routes, `{code, detail}`
errors, `404` for "not yours"). Runnable examples: `docs/requests/part4a.http`
and, for the parent app, `docs/requests/parent/`.

### Cross-cutting (Section A)
- **Login throttling.** `POST /api/v1/auth/login` (and `/auth/register`,
  Section J) are rate-limited per client IP (`AUTH_THROTTLE_RATE`, default
  `10/min`) → `429 {"detail": "Request was throttled. Expected available in N seconds."}`.
- **CORS.** Allowed browser origins come from `CORS_ALLOWED_ORIGINS`
  (default `http://localhost:3000`). The admin dashboard itself calls the API
  server-side through its own proxy (see DECISIONS.md), so CORS is only needed
  by direct browser clients.

#### `GET /api/v1/my-school/`
JWT, any role. Read-only name and branding of the caller's school(s), for
headers and theming (`/schools/` stays platform-only).
```json
{ "school": { "id": 1, "name": "Kampala Demo Primary School",
              "branding": { "logo_url": "…", "primary_color": "#1F6FEB" },
              "supported_languages": ["en", "lg"] },
  "schools": [ { …same shape… } ] }
```
Staff and students: `school` is their school, `schools` = `[school]`.
Parents: `school: null`, `schools` = the schools of their linked children.
platform_admin: `{"school": null, "schools": []}`.

### Section B additions
- `GET /api/v1/privacy/data-requests/` gains `?status=pending|in_progress|completed|rejected`
  and `?request_type=export|correction|deletion` filters (same scoping).

### Section C additions
- `GET /api/v1/students/` gains list filters: `?search=` (case-insensitive
  match on `name` or `class_name`) and `?class_name=` (exact, case-insensitive).
  Scoping is unchanged.

### Section D additions — students, guardians, cards

#### Card UID format (Part 3 must produce exactly this)
`card_uid` is the NFC tag UID as **lowercase hex, two digits per byte, in the
order the reader returns the bytes (Android `Tag.getId()` order), no
separators**. Bytes `04 A2 2B 7C 91 3E 80` → `"04a22b7c913e80"`. 4–32 bytes.
Server-generated UIDs (32-char uuid hex) already fit. Device endpoints
(`/pos/sync/`, `/pos/purchase/`, `/attendance/tap/`, `/pos/p2p-transfer/`)
match `card_uid` **exactly**, so devices must send the normalised form.

#### `POST /api/v1/cards/issue/` and `POST /api/v1/cards/{id}/reissue/` (extended)
Optional `"card_uid"`: accepts upper case and `:`/`-`/space separators and
stores the normalised form. Omitted → server-generated (Part 1 behaviour).
`400 {"card_uid": ["card_uid must be 4-32 bytes of hex…"]}`, or
`400 {"card_uid": ["A card with this card_uid already exists."]}`.

#### `POST /api/v1/cards/{id}/reset-pin/`
JWT, school_admin (own school) / platform_admin (audit-logged). Body
`{ "pin": "4321" }` (4–6 digits). `200`: the Card (never the hash). The card's
`updated_at` changes, so devices get the new hash on their next `?since=`
refresh. Does not unfreeze a card. `409 card_lost` for a lost card.

#### `GET /api/v1/cards/` (extended)
Filters `?student=`, `?status=`, `?card_uid=` (normalised before matching).
Responses gain read-only `student_name`.

#### `POST /api/v1/guardian-verifications/{id}/review/`
JWT, school_admin (verifications of parents linked to their school) /
platform_admin. Body `{ "status": "verified" | "rejected", "review_notes": "…" }`.
`200`: the verification, which now also carries read-only `review_notes`,
`reviewed_by`, `reviewed_at`. Rejecting clears `verified_at`. Parents → `403`;
another school's admin → `404`.

#### `GET /api/v1/users/lookup/?email=<exact>`
JWT, school_admin / platform_admin. Finds an active **parent** account by
exact (case-insensitive) email so it can be linked with `POST /guardians/`.
`200 { id, email, full_name, role, phone_number }`; unknown or not a parent →
`404 not_found`. No partial search, so admins can't enumerate parents.

#### `GET /api/v1/students/{id}/` — behaviour fix (approved)
Parents now get `200` for their own linked children (previously `403`, the
Part 1 quirk) and `404` for anyone else's. Staff scoping is unchanged.

#### `GET /api/v1/students/` (extended)
Also `?card_status=active|frozen|lost|none` and `?low_balance=true` (main
wallet below the school default `low_balance_threshold`, else 2,000).

#### `GET|POST /api/v1/guardians/` (extended)
Read-only `parent_email`, `parent_name`, `parent_phone`, `student_name`,
`verification_status` (null if never submitted). Filters `?student=`,
`?parent=`. Linking a non-parent account → `400`; a school_admin linking a
student of another school → `404` (tenant fix).

#### `GET /api/v1/wallets/`, `GET /api/v1/savings-goals/`, `GET /api/v1/policies/` (extended)
Filters: wallets `?student=`, `?wallet_type=`; savings goals `?student=`,
`?wallet=`; policies `?student=`, `?kind=default|override`. Policies gain
read-only `updated_by_role`, `updated_by_name`, `student_name` (shows which
overrides a parent set).

### Section E additions — staff accounts, device provisioning QR

#### `GET|POST /api/v1/users/`, `GET|PATCH /api/v1/users/{id}/`, `POST /api/v1/users/{id}/set-password/`
JWT, **school_admin** (own school) / platform_admin (`?school=`; audit-logged).
Everyone else `403`. Lists the school's `canteen_staff`, `school_admin` and
`student` (portal) accounts plus `merchant_staff` of merchants approved for the
school. Parents are never listed. Filters `?role=`, `?search=` (email or name).
```json
{ "id": 9, "email": "till@school.test", "full_name": "Peter", "phone_number": "",
  "role": "canteen_staff", "school": 1, "is_active": true, "preferred_language": "en",
  "date_joined": "…", "merchant_id": null, "merchant_name": null }
```
Create body: `{ email, password (≥ 8), role: canteen_staff | merchant_staff | school_admin,
full_name?, phone_number?, merchant? }`. The school is always the admin's own
(platform_admin passes `school`). `merchant_staff` need `merchant` (approved for the
school; created and linked in one transaction, `school: null`).
Errors: `400 role_invalid`, `400 merchant_required`, `400 password_required`,
`403 forbidden` (merchant not approved for your school), `400 {"email": [...]}` (taken).
PATCH accepts only `full_name`, `phone_number`, `preferred_language`, `is_active`
(`409 cannot_deactivate_self`). `set-password` body `{ "password": "…" }`.

#### Device provisioning QR (consumed by the POS app, Part 3)
At registration and token rotation the dashboard shows the raw `device_token`
once, as text and as a QR code whose content is this JSON (UTF-8):
```json
{ "type": "schooldimes_device", "v": 1,
  "api_base_url": "http://192.168.1.20:8000", "device_token": "<raw token>" }
```
`api_base_url` is the backend **origin** (no `/api/v1`) that the device should
use. The admin can edit it before the QR is shown; it defaults to
`NEXT_PUBLIC_DEVICE_API_BASE_URL`, else `NEXT_PUBLIC_API_BASE_URL`.

### Section G additions — platform back-office (`backoffice` app, platform_admin only)

Everyone else gets `403`. Every write is audit-logged.

#### `POST /api/v1/platform/schools/onboard/`
Creates a ready-to-use school in **one transaction**: `School`,
`SchoolSettings`, the default `Policy`, both system wallets
(`school_settlement`, `aggregator_clearing`) and the first `school_admin`.
```json
{ "name": "Mbale Hill Primary", "address": "Mbale",
  "branding": { "logo_url": "https://…/logo.png", "primary_color": "#0E7C66" },
  "supported_languages": ["en", "sw"],
  "policy": { "daily_spend_cap": "5000.00", "weekly_spend_cap": null, "per_transaction_cap": "3000.00",
              "p2p_daily_cap": null, "p2p_enabled": false, "low_balance_threshold": "2000.00" },
  "settings": { "offline_spend_ceiling": "1500.00", "pin_lockout_threshold": 4,
                "device_stale_after_hours": 24, "attendance_notify_guardians": false,
                "attendance_on_canteen_devices": false },
  "admin": { "email": "head@mbalehill.test", "password": "≥ 8 chars", "full_name": "…", "phone_number": "…" } }
```
Only `name` and `admin.email`/`admin.password` are required. Response `201`:
`{ "school": {School}, "admin": {staff user} }`. An admin email that already
exists → `400 {"admin": {"email": [...]}}` and nothing is created.

#### `GET /api/v1/platform/schools/stats/`
`{ "results": [ { id, name, branding, supported_languages, created_at, students,
school_admins, active_cards, active_devices, student_balances_total,
sales_30d_count, sales_30d_collected } ] }` (balances from the wallets, which
equal the ledger; sales exclude rejected POS rows).

#### `GET /api/v1/audit-logs/`, `GET /api/v1/audit-logs/{id}/`
Filters `?school=`, `?action=` (contains), `?actor=`. Newest first.
`{ id, actor, actor_email, actor_role, school, school_name, action, target_type, target_id, details, created_at }`.

#### `GET /api/v1/payments/unmatched-webhooks/`, `POST /api/v1/payments/unmatched-webhooks/{id}/mark-reviewed/`
`?reviewed=true|false`. `{ id, reference, aggregator_ref, reason, payload, reviewed, received_at }`.
Marking reviewed moves no money.

#### Cross-tenant support reads (extended)
platform_admin may narrow these existing lists with `?school=<id>`:
`/pos/devices/`, `/pos/transactions/`, `/cards/`, `/payments/deposits/`
(`/students/` already supported it). They remain read-mostly; platform_admin
writes are audit-logged by the existing mixins.

### Section H additions — student portal

#### `GET|POST|DELETE /api/v1/students/{id}/portal-account/`
JWT, school_admin (own school; other schools `404`) / platform_admin.
POST `{ "email": "…", "password": "≥ 8 chars" }` creates a `student`-role
login linked to this student (`409 portal_account_exists`, `409 email_taken`).
GET → `{ "email", "is_active" }` or `404`. DELETE removes the login (`204`);
the student's wallets, card and history are untouched.

#### `GET /api/v1/student-portal/me/`
JWT, **student** role only (everyone else `403`). Read-only:
```json
{ "student": { "id": 1, "name": "Amina Nakato", "first_name": "Amina", "class_name": "P4" },
  "school": { "id": 1, "name": "…", "branding": {…} },
  "main_balance": "25300.00", "savings_balance": "2000.00",
  "savings_goals": [ {SavingsGoal incl. current_amount, progress_percent, is_reached} ],
  "recent_purchases": [ { "id": 9, "when": "…", "amount": "1700.00", "place": "Simulator bookshop",
                          "items": [ { "description": "Exercise book", "quantity": 1, "line_total": "1200.00" } ] } ],
  "tip": { "title": "…", "body": "…", "language": "en" } }
```
Last 10 non-rejected POS purchases. The tip is in the student's
`preferred_language` (school or platform-wide), falling back to English.

#### Student logins are restricted to an allowlist (all endpoints)
A `student`-role JWT may only call `/me`, `/auth/refresh`, `/auth/logout`,
`/my-school/`, `/student-portal/me/` and `/financial-literacy-tips/`. Every
other endpoint answers `403` for a student login (enforced by the default
authentication class, `core.authentication.SchoolDimesJWTAuthentication`).

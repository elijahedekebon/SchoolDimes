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

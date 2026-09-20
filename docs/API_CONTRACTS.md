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

- Deposits (parent MoMo/bank/USSD), P2P transfers, POS purchases, fee
  top-ups, pooled funds, gift vouchers, scheduled recurring top-ups,
  attendance tap-in, merchant network, dispute/refund flow — **Part 2/3**.
  All of these will call `wallets.services.post_ledger_entry()`; none of
  them get a new ledger model.
- POS app, sales analytics — **Part 3**.
- Parent/admin dashboards, offline mode/sync, biometric matching (the
  `Card.biometric_enrolled` flag exists now; actual capture/matching is a
  client concern) — **Part 4**.

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

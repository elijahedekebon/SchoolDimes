# Parent App Readiness

Every screen of the Flutter parent app (Part 4B) and the exact endpoints it
uses. Part 4A's job was to make this list complete, so **Part 4B should need no
backend work**. All paths are under `/api/v1/` and documented in
`docs/API_CONTRACTS.md`. Every request file uses the seed parent
`parent1@schooldimes.test` / `pw123456` (see `docs/requests/parent/_README.md`).

**Web migration (Django templates + HTMX):** nothing here changed. The web
surfaces moved into Django, and several API views now call shared service
functions instead of holding the logic themselves; every request and
response below is identical (the full API suite is unchanged and green, and
`backend/parents/test_readiness_routes.py` checks every endpoint in this table
still resolves with its method). The only visible difference: `share_url` now
points at the backend origin's `/give/<token>` page (same path).

Status: **P1** = existed in Part 1, **P2** = existed in Part 2, **4A** = added
or extended in Part 4A.

Permissions everywhere: a parent only ever reaches **their own linked
students** (anything else is `404`), and tenant scoping comes from the token,
never from the request.

| Screen (4B section) | Endpoint(s) | Status | Requests |
|---|---|---|---|
| Register (B) | `POST auth/register` | 4A | [auth.http](requests/parent/auth.http) |
| Login / refresh / logout (B) | `POST auth/login`, `POST auth/refresh` (rotates), `POST auth/logout` | P1 (login throttled 4A) | [auth.http](requests/parent/auth.http) |
| KYC-lite submit + status (C) | `POST/GET guardian-verifications/` (`status`, `review_notes`) | P1, review fields 4A | [auth.http](requests/parent/auth.http) |
| Multi-child dashboard (D) | `GET parent/dashboard/` (students, balances, goals, card, 5 recent itemized transactions, unread count, tip) | 4A | [dashboard.http](requests/parent/dashboard.http) |
| Tip card (D) | in the dashboard; or `GET financial-literacy-tips/?language=` | P1 | [dashboard.http](requests/parent/dashboard.http) |
| Child profile | `GET students/{id}/` (parent 403 fixed) | P1, fixed 4A | [dashboard.http](requests/parent/dashboard.http) |
| Transaction history + filters (E) | `GET students/{id}/transactions/?wallet=&entry_type=&direction=&from=&to=` | 4A | [transactions.http](requests/parent/transactions.http) |
| Transaction detail with line items (E) | same rows: `pos.items[]` | 4A | [transactions.http](requests/parent/transactions.http) |
| Spending summary | `GET analytics/students/{id}/spending/` | P2 | [transactions.http](requests/parent/transactions.http) |
| Top-up (F) | `POST payments/deposits/` (idempotent) → `instructions` | P2 | [topups.http](requests/parent/topups.http) |
| Top-up status polling (F) | `GET payments/deposits/{id}/` | P2 | [topups.http](requests/parent/topups.http) |
| Deposit history (F) | `GET payments/deposits/?student=` | P2 | [topups.http](requests/parent/topups.http) |
| One-tap top-up from low-balance alert (F) | notification `payload.action` = `{type: top_up, student_id, wallet_id, suggested_amount}` → `POST payments/deposits/` | P2 | [notifications.http](requests/parent/notifications.http) |
| Recurring top-ups CRUD, pause/resume, re-activate (G) | `GET/POST payments/recurring-topups/`, `PATCH …/{id}/ {active}`, `DELETE …/{id}/` | P2 | [recurring.http](requests/parent/recurring.http) |
| Gift voucher (H) | `POST/GET payments/gift-vouchers/` | P2 | [gifts_and_links.http](requests/parent/gifts_and_links.http) |
| Top-up links create/list/revoke + share (H) | `POST/GET payments/topup-links/`, `POST …/{id}/revoke/`; share `share_url` as-is (`<backend origin>/give/<token>`) | P2, URL 4A | [gifts_and_links.http](requests/parent/gifts_and_links.http) |
| Contributions received (H) | `GET payments/deposits/?from_contributor=true` | 4A | [topups.http](requests/parent/topups.http) |
| Pooled funds list / detail / log (I) | `GET pooled-funds/`, `GET pooled-funds/{id}/` | P2 | [pooled_funds.http](requests/parent/pooled_funds.http) |
| Contribute / create fund (I) | `POST pooled-funds/{id}/contribute/` (poll the deposit), `POST pooled-funds/` | P2 | [pooled_funds.http](requests/parent/pooled_funds.http) |
| Spending controls with school limits (J) | `GET students/{id}/spending-controls/`; edit `POST policies/` / `PATCH policies/{id}/`; options from `product-categories/`, `products/`, `merchants/` | 4A (+P2) | [spending_controls.http](requests/parent/spending_controls.http) |
| Savings move in/out (K) | `POST wallets/{main}/savings/move-in/`, `…/move-out/` | P2 | [savings.http](requests/parent/savings.http) |
| Savings goals CRUD (K) | `GET/POST/PATCH/DELETE savings-goals/` (`?student=` 4A) | P1/P2 | [savings.http](requests/parent/savings.http) |
| Withdrawal window (K) | `GET/PUT wallets/{savings}/savings/withdrawal-window/` | P2 | [savings.http](requests/parent/savings.http) |
| Withdrawal request + payout status (K) | `POST wallets/{savings}/savings/withdraw/`, `GET payments/payouts/?student=` | P2, payouts 4A | [savings.http](requests/parent/savings.http) |
| Card freeze/unfreeze, report lost (L) | `GET cards/?student=`, `POST cards/{id}/freeze/`, `…/unfreeze/`, `…/report-lost/` | P1/P2 | [cards_and_p2p.http](requests/parent/cards_and_p2p.http) |
| P2P history (L) | `GET students/{id}/p2p-history/` (parents may also send: `POST wallets/transfer/`) | P2 | [cards_and_p2p.http](requests/parent/cards_and_p2p.http) |
| Disputes raise / track (M) | `POST disputes/` (body = row's `dispute_target`), `GET disputes/` | P2, target 4A | [disputes.http](requests/parent/disputes.http) |
| Notifications inbox, read, read-all (N) | `GET notifications/?unread=true`, `POST …/{id}/read/`, `POST …/read-all/` | P2 | [notifications.http](requests/parent/notifications.http) |
| Notification preferences (N) | `GET/PATCH notifications/preferences/` (channels, low-balance level per child) | P2 | [notifications.http](requests/parent/notifications.http) |
| Push token (N) | `POST notifications/push-tokens/`, `DELETE …/{token}/` | P2 | [notifications.http](requests/parent/notifications.http) |
| Privacy: my data JSON / CSV (O) | `GET privacy/my-data/`, `?format=csv` | P2 | [privacy.http](requests/parent/privacy.http) |
| Privacy: data requests (O) | `POST/GET privacy/data-requests/` (`retention_notice` on deletion) | P2 | [privacy.http](requests/parent/privacy.http) |
| Profile + language (O) | `GET/PATCH me` | P1 | [auth.http](requests/parent/auth.http) |

## Deep links from notifications

`event_type` → screen, with the payload key that carries the id:

| event_type | open | payload |
|---|---|---|
| `low_balance` | top-up, pre-filled | `action.wallet_id`, `action.suggested_amount` |
| `deposit_confirmed`, `deposit_failed` | top-up status | `deposit_id` |
| `contributor_topup_received`, `gift_received` | child's transactions | `student_id` |
| `recurring_topup_executed` / `_failed` / `_paused` | recurring top-ups | `recurring_topup_id` |
| `savings_goal_reached`, `savings_withdrawal_completed` / `_failed` | savings | `student_id`, `goal_id` / `payout_id` |
| `card_frozen`, `card_unfrozen`, `card_reported_lost`, `card_locked_pin_failures` | card control | `student_id`, `card_id` |
| `p2p_transfer_received` | P2P history | `student_id` |
| `dispute_status_changed` | dispute detail | `dispute_id` |
| `pooled_fund_contribution_confirmed` | pooled fund | `fund_id` |
| `attendance_tap_in` | child | `student_id` |
| `data_request_updated` | privacy | `request_id` |

## Facts the app must respect

- **Money** is a decimal string (`"5000.00"`, UGX); never parse to a float.
- **Idempotency**: generate one UUID per user action for deposits, gift
  vouchers, fund contributions, withdrawals and fee payments; reuse it on a
  retry, and only make a new one for a new action.
- **Errors**: `{code, detail}`; `detail` is already translated (send
  `Accept-Language: en|lg|sw`). `422` debit refusals add `violations`.
- **Tokens**: access 30 min, refresh 7 days with rotation (store the new
  refresh token every time). Logout = `POST auth/logout` + delete push token.
- **KYC**: the backend currently enforces no feature limits for unverified
  parents; show the status, don't invent restrictions.

"""Regenerates docs/requests/*.http (VS Code REST Client): python docs/requests/_generate.py"""
from pathlib import Path

OUT = Path(__file__).resolve().parent
OUT.mkdir(parents=True, exist_ok=True)

PRELUDE = """# SchoolDimes Part 2 -- {title}
# VS Code "REST Client" extension (humao.rest-client). Click "Send Request".
# Prerequisites: stack running (docker compose up) and `python manage.py seed_demo`.
# IDs below are placeholders: look real ones up with the GET requests
# (e.g. GET {{{{baseUrl}}}}/students/ or /wallets/) and edit the @variables.

@baseUrl = http://localhost:8000/api/v1
@password = pw123456
@parentEmail = parent1@schooldimes.test
@parent2Email = parent2@schooldimes.test
@adminEmail = admin@kampaladps.schooldimes.test
@merchantStaffEmail = shop@ntindabookshop.schooldimes.test
# JWTs captured from the login requests below (send those first):
@parentToken = {{{{parentLogin.response.body.access}}}}
@adminToken = {{{{adminLogin.response.body.access}}}}
@shopToken = {{{{shopLogin.response.body.access}}}}
{variables}
### Log in as parent1 (guardian of Amina + Brian)
# @name parentLogin
POST {{{{baseUrl}}}}/auth/login
Content-Type: application/json

{{"email": "{{{{parentEmail}}}}", "password": "{{{{password}}}}"}}

### Log in as the Kampala school admin
# @name adminLogin
POST {{{{baseUrl}}}}/auth/login
Content-Type: application/json

{{"email": "{{{{adminEmail}}}}", "password": "{{{{password}}}}"}}
"""

DEVICE_VARS = """
# Paste the raw tokens printed by `python manage.py seed_demo` (they rotate on every run):
@canteenToken = PASTE_CANTEEN_DEVICE_TOKEN
@merchantToken = PASTE_MERCHANT_DEVICE_TOKEN
@attendanceToken = PASTE_ATTENDANCE_DEVICE_TOKEN
"""


def req(title, method, path, auth="parent", body=None, extra_headers=""):
    lines = [f"\n### {title}", f"{method} {{{{baseUrl}}}}{path}"]
    if auth == "parent":
        lines.append("Authorization: Bearer {{parentToken}}")
    elif auth == "admin":
        lines.append("Authorization: Bearer {{adminToken}}")
    elif auth in ("canteen", "merchant", "attendance"):
        lines.append(f"Authorization: Device {{{{{auth}Token}}}}")
    elif auth.startswith("raw:"):
        lines.append(auth[4:])
    if extra_headers:
        lines.append(extra_headers)
    if body is not None:
        lines.append("Content-Type: application/json")
        lines.append("")
        lines.append(body.strip())
    return "\n".join(lines) + "\n"


FILES = {}

FILES["payments.http"] = ("Payments (Section A)", """
@walletId = 1
@studentId = 1
@depositId = 1
@linkId = 1
@recurringId = 1
""", [
    req("My students' wallets (find @walletId)", "GET", "/wallets/"),
    req("Initiate a top-up (mock: phones ending 999 are declined)", "POST", "/payments/deposits/", body="""
{"wallet": {{walletId}}, "amount": "5000", "channel": "momo", "payer_phone": "0772000111", "idempotency_key": "{{$guid}}"}"""),
    req("Same request with a FIXED key twice -> second answer is 200 with the same deposit", "POST", "/payments/deposits/", body="""
{"wallet": {{walletId}}, "amount": "3000", "channel": "ussd", "idempotency_key": "demo-fixed-key-1"}"""),
    req("Poll a deposit", "GET", "/payments/deposits/{{depositId}}/"),
    req("Deposit history (filter by student / status / purpose)", "GET", "/payments/deposits/?student={{studentId}}&status=pending"),
    req("School admin view of deposits", "GET", "/payments/deposits/", auth="admin"),
    req("Create a contributor top-up link", "POST", "/payments/topup-links/", body='{"student": {{studentId}}}'),
    req("List my top-up links", "GET", "/payments/topup-links/"),
    req("Revoke a link", "POST", "/payments/topup-links/{{linkId}}/revoke/"),
    req("Send a gift voucher", "POST", "/payments/gift-vouchers/", body="""
{"student": {{studentId}}, "amount": "2500", "message": "Happy birthday!", "channel": "momo", "payer_phone": "0772000111", "idempotency_key": "{{$guid}}"}"""),
    req("Gift vouchers (sent + received)", "GET", "/payments/gift-vouchers/"),
    req("Create a weekly recurring top-up (Mondays 08:00 Kampala)", "POST", "/payments/recurring-topups/", body="""
{"student": {{studentId}}, "amount": "4000", "channel": "momo", "payer_phone": "0772000111", "frequency": "weekly", "day_of_week": 0}"""),
    req("List recurring top-ups", "GET", "/payments/recurring-topups/"),
    req("Pause a recurring top-up", "PATCH", "/payments/recurring-topups/{{recurringId}}/", body='{"active": false}'),
    req("Delete a recurring top-up", "DELETE", "/payments/recurring-topups/{{recurringId}}/"),
    """
### Aggregator webhook -- simplest from a terminal instead:
###   python manage.py mock_webhook --list
###   python manage.py mock_webhook SD-DEP-XXXX            (or --fail)
### A hand-made request below will get 401 unless the signature matches
### HMAC-SHA256(PAYMENT_AGGREGATOR_WEBHOOK_SECRET, exact body).
POST {{baseUrl}}/payments/webhook/
Content-Type: application/json
X-SchoolDimes-Signature: not-a-valid-signature

{"reference": "SD-DEP-XXXX", "aggregator_ref": "", "status": "successful", "amount": "5000.00", "failure_reason": ""}
""",
])

FILES["public.http"] = ("Public contributor endpoints (Section A)", """
# Paste TOPUP_LINK_TOKEN from the seed_demo output:
@linkToken = PASTE_TOPUP_LINK_TOKEN
@reference = SD-DEP-XXXX
""", [
    req("What a contributor sees (first name + school only)", "GET", "/public/topup-links/{{linkToken}}/", auth="none"),
    req("Contributor top-up", "POST", "/public/topup-links/{{linkToken}}/deposits/", auth="none", body="""
{"contributor": {"name": "Jjajja Nalongo", "phone_number": "0701000222", "relationship_label": "Grandmother"},
 "amount": "3000", "channel": "ussd", "idempotency_key": "{{$guid}}"}"""),
    req("Poll a contributor deposit", "GET", "/public/topup-links/{{linkToken}}/deposits/{{reference}}/", auth="none"),
    req("Contributor gift voucher", "POST", "/public/topup-links/{{linkToken}}/gift-vouchers/", auth="none", body="""
{"contributor": {"name": "Uncle Tom", "email": "tom@example.com"}, "amount": "2000", "message": "Buy a book!",
 "channel": "momo", "payer_phone": "0701000333", "idempotency_key": "{{$guid}}"}"""),
])

FILES["pooled_funds.http"] = ("Pooled funds (Section B)", "\n@fundId = 1\n", [
    req("List funds of my children's schools", "GET", "/pooled-funds/"),
    req("Create a fund", "POST", "/pooled-funds/", body="""
{"title": "P4 sports day", "purpose": "Medals and water", "group_label": "P4", "target_amount": "30000", "deadline": "2026-12-01"}"""),
    req("Fund detail with the transparent contribution log", "GET", "/pooled-funds/{{fundId}}/"),
    req("Contribute (confirm it with manage.py mock_webhook SD-PF-...)", "POST", "/pooled-funds/{{fundId}}/contribute/", body="""
{"amount": "5000", "channel": "momo", "payer_phone": "0772000111", "idempotency_key": "{{$guid}}"}"""),
    req("Close (creator or school admin)", "POST", "/pooled-funds/{{fundId}}/close/"),
    req("Disburse to the school (school admin only)", "POST", "/pooled-funds/{{fundId}}/disburse/", auth="admin", body="""
{"amount": "5000", "destination": "school_settlement", "description": "Bus hire deposit"}"""),
    req("Disburse externally to a phone (mock: phones ending 998 fail and are reversed)", "POST", "/pooled-funds/{{fundId}}/disburse/", auth="admin", body="""
{"amount": "1000", "destination": "external", "description": "Teacher gift", "phone_number": "0772111222"}"""),
])

FILES["wallets.http"] = ("Wallets: policy, savings, P2P, cards (Section C)", """
@walletId = 1
@savingsWalletId = 2
@studentId = 1
@recipientStudentId = 3
@cardId = 1
@policyId = 1
@alertId = 1
@goalId = 1
""", [
    req("Product categories", "GET", "/product-categories/"),
    req("Create a category (admin)", "POST", "/product-categories/", auth="admin", body='{"name": "Fruit", "is_unhealthy": false}'),
    req("Products", "GET", "/products/?active=true"),
    req("Create a product (admin)", "POST", "/products/", auth="admin", body='{"name": "Banana", "category": 1, "price": "200"}'),
    req("Policies (school default + overrides) as admin", "GET", "/policies/", auth="admin"),
    req("Tighten the school default (admin)", "PATCH", "/policies/{{policyId}}/", auth="admin", body='{"daily_spend_cap": "6000", "p2p_daily_cap": "3000"}'),
    req("Parent creates an override for their child (tighten only)", "POST", "/policies/", body='{"student": {{studentId}}, "daily_spend_cap": "3000", "blocked_categories": [3]}'),
    req("Parent tries to LOOSEN -> 400 policy_cannot_loosen", "POST", "/policies/", body='{"student": {{studentId}}, "daily_spend_cap": "999999"}'),
    req("Effective policy for a student", "GET", "/students/{{studentId}}/effective-policy/"),
    req("Move 2,000 main -> savings", "POST", "/wallets/{{walletId}}/savings/move-in/", body='{"amount": "2000"}'),
    req("Move 500 savings -> main", "POST", "/wallets/{{walletId}}/savings/move-out/", body='{"amount": "500"}'),
    req("Savings goals with progress", "GET", "/savings-goals/"),
    req("Open a withdrawal window (guardian)", "PUT", "/wallets/{{savingsWalletId}}/savings/withdrawal-window/", body="""
{"withdrawal_window_start": "2026-01-01T00:00:00Z", "withdrawal_window_end": "2027-12-31T00:00:00Z"}"""),
    req("Check the window", "GET", "/wallets/{{savingsWalletId}}/savings/withdrawal-window/"),
    req("Withdraw savings to mobile money (mock: 998 fails and is reversed)", "POST", "/wallets/{{savingsWalletId}}/savings/withdraw/", body="""
{"amount": "1000", "phone_number": "0772000111", "idempotency_key": "{{$guid}}"}"""),
    req("P2P transfer (guardian of the sender)", "POST", "/wallets/transfer/", body="""
{"sender_student": {{studentId}}, "recipient_student": {{recipientStudentId}}, "amount": "500", "note": "lunch money"}"""),
    req("P2P history", "GET", "/students/{{studentId}}/p2p-history/"),
    req("P2P pattern alerts (admin)", "GET", "/p2p-alerts/?status=open", auth="admin"),
    req("Review an alert (admin)", "POST", "/p2p-alerts/{{alertId}}/review/", auth="admin", body='{"status": "reviewed", "review_notes": "Spoke to the class teacher"}'),
    req("My children's cards", "GET", "/cards/"),
    req("Freeze a card (notifies the other guardians)", "POST", "/cards/{{cardId}}/freeze/"),
    req("Unfreeze", "POST", "/cards/{{cardId}}/unfreeze/"),
    req("Report a card lost (then the admin reissues)", "POST", "/cards/{{cardId}}/report-lost/"),
    req("Reissue (admin)", "POST", "/cards/{{cardId}}/reissue/", auth="admin", body='{"pin": "2468"}'),
])

FILES["pos.http"] = ("Canteen POS + offline sync (Section D)", DEVICE_VARS + """
@deviceId = 1
@cardUid = PASTE_A_CARD_UID_FROM_THE_CACHE
@recipientCardUid = PASTE_ANOTHER_CARD_UID
@txnId = 1
""", [
    req("Register a device (admin) -- the token is shown ONCE", "POST", "/pos/devices/register/", auth="admin", body='{"device_name": "Till 2", "device_role": "canteen"}'),
    req("List devices", "GET", "/pos/devices/", auth="admin"),
    req("Stale devices", "GET", "/pos/devices/?stale=true", auth="admin"),
    req("Rotate a device token", "POST", "/pos/devices/{{deviceId}}/rotate-token/", auth="admin"),
    req("Revoke a device", "POST", "/pos/devices/{{deviceId}}/revoke/", auth="admin"),
    req("School settings (offline ceiling etc.)", "GET", "/school-settings/", auth="admin"),
    req("Change the offline spend ceiling", "PATCH", "/school-settings/", auth="admin", body='{"offline_spend_ceiling": "3000"}'),
    req("Full offline cache (as the canteen device)", "GET", "/pos/cache/", auth="canteen"),
    req("Incremental refresh", "GET", "/pos/cache/?since=2026-09-30T00:00:00Z", auth="canteen"),
    req("Sync an offline batch (replay it unchanged to see 'duplicate')", "POST", "/pos/sync/", auth="canteen", body="""
{"transactions": [
  {"idempotency_key": "http-demo-sale-1", "card_uid": "{{cardUid}}", "amount": "3500.00",
   "items": [{"product_id": 1, "quantity": 1, "unit_price": "3000.00"},
             {"description": "Mandazi", "category_id": 2, "quantity": 1, "unit_price": "500.00"}],
   "device_local_timestamp": "2026-09-30T12:45:00+03:00", "pin_verified": true}
 ],
 "pin_failures": []}"""),
    req("Online purchase (authorize_debit enforced; PIN checked server-side)", "POST", "/pos/purchase/", auth="canteen", body="""
{"idempotency_key": "{{$guid}}", "card_uid": "{{cardUid}}", "amount": "500", "pin": "1001",
 "items": [{"description": "Chapati", "quantity": 1, "unit_price": "500"}]}"""),
    req("P2P at the till (sender card + PIN)", "POST", "/pos/p2p-transfer/", auth="canteen", body="""
{"idempotency_key": "{{$guid}}", "sender_card_uid": "{{cardUid}}", "pin": "1001", "recipient_card_uid": "{{recipientCardUid}}", "amount": "300"}"""),
    req("All POS transactions (admin)", "GET", "/pos/transactions/?sync_status=shortfall", auth="admin"),
    req("Review queue: shortfalls + flagged sales", "GET", "/pos/shortfalls/", auth="admin"),
    req("Resolve: write off / recover_from_next_topup / charge_guardian / accept", "POST", "/pos/shortfalls/{{txnId}}/resolve/", auth="admin", body="""
{"resolution": "recover_from_next_topup", "review_notes": "Double-spend across tills"}"""),
])

FILES["attendance.http"] = ("Attendance tap-in (Section F)", DEVICE_VARS + """
@cardUid = PASTE_A_CARD_UID
@studentId = 1
""", [
    req("Single tap", "POST", "/attendance/tap/", auth="attendance", body="""
{"idempotency_key": "{{$guid}}", "card_uid": "{{cardUid}}", "direction": "in", "device_local_timestamp": "2026-09-30T07:30:00+03:00"}"""),
    req("Offline batch (the repeated key comes back 'duplicate')", "POST", "/attendance/tap/", auth="attendance", body="""
{"taps": [
  {"idempotency_key": "http-tap-1", "card_uid": "{{cardUid}}", "direction": "in", "device_local_timestamp": "2026-09-30T07:31:00+03:00"},
  {"idempotency_key": "http-tap-1", "card_uid": "{{cardUid}}", "direction": "in", "device_local_timestamp": "2026-09-30T07:31:00+03:00"},
  {"idempotency_key": "http-tap-2", "card_uid": "{{cardUid}}", "direction": "out", "device_local_timestamp": "2026-09-30T16:05:00+03:00"}
]}"""),
    req("Attendance for a day (admin)", "GET", "/attendance/?date=2026-09-30", auth="admin"),
    req("My child's attendance (guardian)", "GET", "/students/{{studentId}}/attendance/?from=2026-09-01&to=2026-09-30"),
])

FILES["merchants.http"] = ("Merchant network (Section G)", DEVICE_VARS + """
@merchantId = 1
@merchantStaffUserId = 1
""", [
    """
### Log in as the merchant's staff user
# @name shopLogin
POST {{baseUrl}}/auth/login
Content-Type: application/json

{"email": "{{merchantStaffEmail}}", "password": "{{password}}"}
""",
    req("Merchants (admin sees all, to approve shared ones)", "GET", "/merchants/", auth="admin"),
    req("Register a merchant (auto-approved for my school)", "POST", "/merchants/", auth="admin", body='{"name": "Kisaasi Tailors", "category": "tailor", "contact_phone": "0772400400"}'),
    req("Approve for my school", "POST", "/merchants/{{merchantId}}/approve/", auth="admin"),
    req("Suspend for my school", "POST", "/merchants/{{merchantId}}/suspend/", auth="admin"),
    req("Link a merchant_staff user", "POST", "/merchants/{{merchantId}}/staff/", auth="admin", body='{"user": {{merchantStaffUserId}}}'),
    req("Merchants my child may use (parent)", "GET", "/merchants/"),
    req("Register a merchant device (admin)", "POST", "/pos/devices/register/", auth="admin", body='{"device_name": "Shop till", "device_role": "merchant", "merchant": {{merchantId}}}'),
    req("Merchant cache (cards of every approving school, merchant products only)", "GET", "/pos/cache/", auth="merchant"),
    req("Statement as merchant staff (all schools)", "GET", "/merchants/{{merchantId}}/statement/", auth="raw:Authorization: Bearer {{shopToken}}"),
    req("Statement as school admin (own school only)", "GET", "/merchants/{{merchantId}}/statement/?from=2026-09-01&to=2026-09-30", auth="admin"),
    req("Parent blocks a merchant for their child", "POST", "/policies/", body='{"student": 1, "blocked_merchants": [{{merchantId}}]}'),
])

FILES["fees.http"] = ("Fee top-ups (Section E)", "\n@studentId = 1\n@feeCategoryId = 1\n", [
    req("Fee categories", "GET", "/fee-categories/?active=true"),
    req("Fees applicable to a class", "GET", "/fee-categories/?class_name=P4"),
    req("Create a fee category (admin)", "POST", "/fee-categories/", auth="admin", body="""
{"name": "Swimming", "amount_type": "range", "min_amount": "2000", "max_amount": "10000", "applicable_classes": []}"""),
    req("Pay a fee (guardian; exempt from snack caps)", "POST", "/fees/pay/", body="""
{"student": {{studentId}}, "fee_category": {{feeCategoryId}}, "idempotency_key": "{{$guid}}"}"""),
    req("Pay a range fee with an amount", "POST", "/fees/pay/", body='{"student": {{studentId}}, "fee_category": 2, "amount": "2500"}'),
    req("Payment history per student", "GET", "/fees/payments/?student={{studentId}}"),
    req("Payment history per category (admin)", "GET", "/fees/payments/?fee_category={{feeCategoryId}}", auth="admin"),
])

FILES["disputes.http"] = ("Disputes & refunds (Section H)", "\n@txnId = 1\n@disputeId = 1\n@ledgerEntryId = 1\n", [
    req("Raise a dispute on a POS sale", "POST", "/disputes/", body="""
{"pos_transaction": {{txnId}}, "reason_category": "wrong_amount", "description": "Only had one plate"}"""),
    req("Raise a dispute on a fee payment (ledger entry)", "POST", "/disputes/", body="""
{"ledger_entry": {{ledgerEntryId}}, "reason_category": "not_received", "description": "Trip was cancelled"}"""),
    req("My disputes", "GET", "/disputes/"),
    req("School queue (admin)", "GET", "/disputes/?status=open", auth="admin"),
    req("Start review (admin)", "POST", "/disputes/{{disputeId}}/review/", auth="admin"),
    req("Resolve with a partial refund (admin)", "POST", "/disputes/{{disputeId}}/resolve/", auth="admin", body="""
{"outcome": "refund", "refund_amount": "1000", "resolution_notes": "Overcharged by one plate"}"""),
    req("Resolve by denying (admin)", "POST", "/disputes/{{disputeId}}/resolve/", auth="admin", body='{"outcome": "deny", "resolution_notes": "Receipt confirms two plates"}'),
])

FILES["notifications.http"] = ("Notifications (Section I)", "\n@notificationId = 1\n@studentId = 1\n", [
    req("My notifications (with unread_count)", "GET", "/notifications/"),
    req("Unread only", "GET", "/notifications/?unread=true"),
    req("Mark one read", "POST", "/notifications/{{notificationId}}/read/"),
    req("Mark all read", "POST", "/notifications/read-all/"),
    req("Preferences", "GET", "/notifications/preferences/"),
    req("Update preferences + per-child low-balance level", "PUT", "/notifications/preferences/", body="""
{"in_app_enabled": true, "sms_enabled": true, "push_enabled": true, "low_balance_thresholds": {"{{studentId}}": "2500"}}"""),
    req("Register a push token", "POST", "/notifications/push-tokens/", body='{"token": "demo-fcm-token", "platform": "android"}'),
    req("List push tokens", "GET", "/notifications/push-tokens/"),
    req("Remove a push token (logout)", "DELETE", "/notifications/push-tokens/demo-fcm-token/"),
])

FILES["privacy.http"] = ("Privacy (Section J)", "\n@studentId = 1\n@requestId = 1\n", [
    req("My data (JSON)", "GET", "/privacy/my-data/"),
    req("My data (CSV download)", "GET", "/privacy/my-data/?format=csv"),
    req("Request a correction", "POST", "/privacy/data-requests/", body="""
{"request_type": "correction", "subject": "student", "student": {{studentId}}, "details": "Date of birth should be 2016-03-04"}"""),
    req("Request deletion of my own account", "POST", "/privacy/data-requests/", body='{"request_type": "deletion", "subject": "self", "details": "Moving abroad"}'),
    req("My requests", "GET", "/privacy/data-requests/"),
    req("School's requests (admin)", "GET", "/privacy/data-requests/", auth="admin"),
    req("Handle a request (admin; completing a deletion redacts PII, keeps the ledger)", "POST", "/privacy/data-requests/{{requestId}}/handle/", auth="admin", body="""
{"status": "in_progress", "notes": "Checking with the class teacher"}"""),
])

FILES["analytics.http"] = ("Analytics & reconciliation (Section K)", "\n@studentId = 1\n@from = 2026-09-01\n@to = 2026-09-30\n", [
    req("Sales summary", "GET", "/analytics/sales-summary/?from={{from}}&to={{to}}", auth="admin"),
    req("Best sellers", "GET", "/analytics/best-sellers/?from={{from}}&to={{to}}&limit=5", auth="admin"),
    req("Peak hours (Kampala)", "GET", "/analytics/peak-hours/?from={{from}}&to={{to}}", auth="admin"),
    req("Category breakdown + unhealthy share", "GET", "/analytics/category-breakdown/?from={{from}}&to={{to}}", auth="admin"),
    req("One student's spending (admin)", "GET", "/analytics/students/{{studentId}}/spending/?from={{from}}&to={{to}}", auth="admin"),
    req("One student's spending (guardian)", "GET", "/analytics/students/{{studentId}}/spending/"),
    req("Daily reconciliation", "GET", "/analytics/reconciliation/?date={{to}}", auth="admin"),
])

for name, (title, variables, requests) in FILES.items():
    text = PRELUDE.format(title=title, variables=variables.replace("{", "{").rstrip() + "\n") + "".join(requests)
    (OUT / name).write_text(text, encoding="utf-8")
    print("wrote", name, text.count("\n###"))

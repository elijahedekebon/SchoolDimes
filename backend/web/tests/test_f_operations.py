"""Section F: fees, attendance, pooled funds, disputes, P2P alerts, data requests, tips, payment issues."""
from decimal import Decimal

import pytest

from attendance.models import AttendanceRecord
from content.models import FinancialLiteracyTip
from disputes.models import Dispute
from disputes.services import raise_dispute
from fees.models import FeeCategory, FeePayment
from pooled_funds.models import PooledFund
from wallets.models import P2PAlert, Wallet

from .conftest import hx

pytestmark = pytest.mark.django_db

F_PAGES = ("/school/fees", "/school/attendance", "/school/pooled-funds", "/school/disputes", "/school/p2p-alerts",
           "/school/privacy", "/school/tips", "/school/payment-issues")


def main_balance(student):
    return Wallet.objects.get(student=student, wallet_type="main").cached_balance


def test_f_pages_render(admin_a_web, pos_a):
    for url in F_PAGES:
        r = admin_a_web.get(url)
        assert r.status_code == 200 and 'data-testid="error-alert"' not in r.content.decode(), url


def test_fee_category_and_pay_fee_idempotent(admin_a_web, school_a, funded_student_a1):
    admin_a_web.post("/school/fees/categories/new", {"name": "Exam", "amount_type": "fixed", "fixed_amount": "2500",
                                                     "applicable_classes": "P4, P5", "active": "1"}, **hx())
    cat = FeeCategory.objects.get(name="Exam")
    assert cat.applicable_classes == ["P4", "P5"] and cat.school == school_a
    dialog = admin_a_web.get(f"/school/fees/categories/{cat.pk}/pay", **hx()).content.decode()
    key = dialog.split('name="idempotency_key" value="')[1].split('"')[0]
    before = main_balance(funded_student_a1)
    for _ in range(2):  # a double click can't pay twice
        r = admin_a_web.post(f"/school/fees/categories/{cat.pk}/pay",
                             {"student": funded_student_a1.pk, "idempotency_key": key}, **hx())
        assert "sd-close" in r["HX-Trigger"]
    assert FeePayment.objects.count() == 1
    assert main_balance(funded_student_a1) == before - Decimal("2500")
    csv = admin_a_web.get("/school/fees/payments/export").content.decode().splitlines()
    assert csv[0] == "id,created_at,student_name,fee_category_name,amount,status,ledger_reference" and len(csv) == 2


def test_pay_fee_other_school_student_is_refused(admin_a_web, school_a, student_b1):
    cat = FeeCategory.objects.create(school=school_a, name="Trip", amount_type="fixed", fixed_amount="1000")
    r = admin_a_web.post(f"/school/fees/categories/{cat.pk}/pay", {"student": student_b1.pk, "idempotency_key": "k"}, **hx())
    assert r.status_code == 404 and not FeePayment.objects.exists()


def test_attendance_register_and_csv(admin_a_web, student_a1, student_a2, school_admin_a, school_a):
    from django.utils import timezone

    from cards.services import issue_card
    from pos.services import register_device

    device, _ = register_device(school_admin_a, school=school_a, device_name="Gate", device_role="attendance")
    card = issue_card(student_a1, "1234")
    AttendanceRecord.objects.create(school=school_a, student=student_a1, card=card, device=device, direction="in",
                                    device_local_timestamp=timezone.now(), idempotency_key="a1")
    body = admin_a_web.get("/school/attendance").content.decode()
    assert "1 of 2 present" in body
    csv = admin_a_web.get("/school/attendance/export", {"class_name": "P4"})
    assert csv["Content-Disposition"].endswith('-P4.csv"')
    lines = csv.content.decode().splitlines()
    assert lines[0] == "student,class,status,first_in,last_out,taps" and any(",present," in line for line in lines)
    per = admin_a_web.get("/school/attendance", {"student": student_a1.pk}, **hx("attendance_student")).content.decode()
    assert "Gate" in per


def test_pooled_fund_create_close_disburse_limits(admin_a_web, school_a, school_admin_a):
    from conftest import fund_wallet

    admin_a_web.post("/school/pooled-funds/new", {"title": "Zoo trip", "group_label": "P4", "target_amount": "50000"}, **hx())
    fund = PooledFund.objects.get(title="Zoo trip")
    fund_wallet(fund.wallet, "3000")
    drawer = admin_a_web.get(f"/school/pooled-funds/{fund.pk}", **hx()).content.decode()
    assert "UGX 3,000" in drawer and "Disburse" in drawer
    body = admin_a_web.post(f"/school/pooled-funds/{fund.pk}/disburse",
                            {"amount": "5000", "destination": "school_settlement", "description": "bus",
                             "idempotency_key": "d1"}, **hx()).content.decode()
    assert "More than the fund holds" in body
    admin_a_web.post(f"/school/pooled-funds/{fund.pk}/disburse",
                     {"amount": "2000", "destination": "school_settlement", "description": "bus",
                      "idempotency_key": "d2"}, **hx())
    fund.wallet.refresh_from_db()
    assert fund.wallet.cached_balance == Decimal("1000")
    admin_a_web.post(f"/school/pooled-funds/{fund.pk}/close", **hx())
    fund.refresh_from_db()
    assert fund.status == "closed"


def test_dispute_refund_changes_balance_and_cannot_exceed(admin_a_web, admin_b_web, pos_a, parent_user):
    dispute = raise_dispute(parent_user, reason_category="wrong_amount", pos_transaction_id=pos_a["sale_id"])
    assert admin_b_web.get(f"/school/disputes/{dispute.pk}", **hx()).status_code == 404
    page = admin_a_web.get("/school/disputes", {"open": dispute.pk}).content.decode()
    assert f'hx-get="/school/disputes/{dispute.pk}"' in page and 'hx-trigger="load"' in page
    student = pos_a["student"]
    before = main_balance(student)
    body = admin_a_web.post(f"/school/disputes/{dispute.pk}/resolve",
                            {"outcome": "refund", "refund_amount": "3000.01"}, **hx()).content.decode()
    assert "More than can be refunded" in body
    admin_a_web.post(f"/school/disputes/{dispute.pk}/review", **hx())
    r = admin_a_web.post(f"/school/disputes/{dispute.pk}/resolve", {"outcome": "refund", "refund_amount": "1000",
                                                                     "resolution_notes": "sorry"}, **hx())
    assert "sd-close" in r["HX-Trigger"]
    assert main_balance(student) == before + Decimal("1000")
    dispute.refresh_from_db()
    assert dispute.status == "resolved_refunded"


def test_p2p_alert_review(admin_a_web, admin_b_web, student_a1, school_a):
    alert = P2PAlert.objects.create(school=school_a, student=student_a1, rule="many_distinct_senders",
                                    details={"distinct_senders": 4})
    body = admin_a_web.get("/school/p2p-alerts").content.decode()
    assert "Received from many different students" in body and "distinct senders: 4" in body
    assert admin_b_web.get(f"/school/p2p-alerts/{alert.pk}/review", **hx()).status_code == 404
    admin_a_web.post(f"/school/p2p-alerts/{alert.pk}/review", {"status": "reviewed", "review_notes": "ok"}, **hx())
    alert.refresh_from_db()
    assert alert.status == "reviewed"
    assert "Every transfer" in admin_a_web.get(f"/school/p2p-alerts/{alert.pk}/history", **hx()).content.decode()


def test_data_request_deletion_shows_retention_notice(admin_a_web, guardian_link_a1, parent_user, student_a1):
    from privacy.services import create_request

    req = create_request(parent_user, request_type="deletion", subject="self")
    body = admin_a_web.get("/school/privacy").content.decode()
    assert "Financial records" in body and "Deletion" in body
    dialog = admin_a_web.get(f"/school/privacy/{req.pk}/handle", **hx()).content.decode()
    assert "This can&#x27;t be undone" in dialog or "This can't be undone" in dialog
    admin_a_web.post(f"/school/privacy/{req.pk}/handle", {"status": "in_progress", "notes": "on it"}, **hx())
    req.refresh_from_db()
    assert req.status == "in_progress"


def test_tips_crud_scoped(admin_a_web, admin_b_web, school_a):
    FinancialLiteracyTip.objects.create(school=None, title="Global", body="b", language="en")
    admin_a_web.post("/school/tips/new", {"title": "Save a bit", "body": "Every week", "language": "lg"}, **hx())
    tip = FinancialLiteracyTip.objects.get(title="Save a bit")
    assert tip.school == school_a and tip.language == "lg"
    body = admin_a_web.get("/school/tips").content.decode()
    assert "Global" in body and "Platform-wide" in body and "Save a bit" in body
    assert "Save a bit" not in admin_b_web.get("/school/tips").content.decode()
    glob = FinancialLiteracyTip.objects.get(title="Global")
    assert admin_a_web.get(f"/school/tips/{glob.pk}/delete", **hx()).status_code == 404  # platform tip, read-only here
    admin_a_web.post(f"/school/tips/{tip.pk}/delete", **hx())
    assert not FinancialLiteracyTip.objects.filter(pk=tip.pk).exists()


def test_payment_issues_lists_failed_deposits(admin_a_web, admin_b_web, funded_student_a1, parent_user):
    from payments.models import Deposit
    from payments.services import create_parent_deposit, mock_confirm

    wallet = Wallet.objects.get(student=funded_student_a1, wallet_type="main")
    dep, _ = create_parent_deposit(parent_user, wallet=wallet, amount="1000", channel="momo",
                                   payer_phone="0700000000", idempotency_key="x1")
    mock_confirm(dep, success=False, failure_reason="declined")
    assert Deposit.objects.get(pk=dep.pk).status == "failed"
    assert dep.reference in admin_a_web.get("/school/payment-issues").content.decode()
    assert dep.reference not in admin_b_web.get("/school/payment-issues").content.decode()

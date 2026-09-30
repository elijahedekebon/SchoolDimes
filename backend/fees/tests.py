from decimal import Decimal

import pytest

from conftest import assert_books_balanced, client_for
from fees.models import FeeCategory, FeePayment
from policies.services import get_school_policy
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_student_wallet, get_system_wallet


@pytest.fixture
def exam_fee(admin_a_client):
    resp = admin_a_client.post("/api/v1/fee-categories/", {
        "name": "Exam fee", "amount_type": "fixed", "fixed_amount": "6000", "applicable_classes": ["P4"],
    }, format="json")
    assert resp.status_code == 201, resp.data
    return FeeCategory.objects.get(pk=resp.data["id"])


@pytest.fixture
def trip_fee(school_a):
    return FeeCategory.objects.create(school=school_a, name="Trip", amount_type="range",
                                      min_amount=Decimal("1000"), max_amount=Decimal("5000"))


def pay(client, student, category, amount=None, key=None):
    body = {"student": student.pk, "fee_category": category.pk}
    if amount is not None:
        body["amount"] = amount
    if key:
        body["idempotency_key"] = key
    return client.post("/api/v1/fees/pay/", body, format="json")


@pytest.mark.django_db
class TestFees:
    def test_guardian_pays_fee_into_settlement(self, parent_client, funded_student_a1, exam_fee, school_a):
        resp = pay(parent_client, funded_student_a1, exam_fee, key="f1")
        assert resp.status_code == 201, resp.data
        assert resp.data["amount"] == "6000.00" and resp.data["ledger_reference"].startswith("fee:")
        assert get_student_wallet(funded_student_a1).cached_balance == Decimal("4000")
        assert get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT).cached_balance == Decimal("6000")
        assert LedgerEntry.objects.filter(reference_id=resp.data["ledger_reference"], entry_type="fee_payment").count() == 2
        replay = pay(parent_client, funded_student_a1, exam_fee, key="f1")
        assert replay.status_code == 200 and FeePayment.objects.count() == 1
        assert_books_balanced(school_a)

    def test_fees_exempt_from_snack_caps_but_not_freeze_or_balance(self, parent_client, funded_student_a1, exam_fee, trip_fee, school_a):
        policy = get_school_policy(school_a)
        policy.daily_spend_cap = Decimal("1000")
        policy.per_transaction_cap = Decimal("500")
        policy.save()
        assert pay(parent_client, funded_student_a1, exam_fee).status_code == 201  # 6000 > caps: fine
        short = pay(parent_client, funded_student_a1, trip_fee, amount="5000")
        assert short.status_code == 422 and short.data["code"] == "insufficient_funds"
        card = funded_student_a1.cards.get()
        card.status = "frozen"
        card.save()
        frozen = pay(parent_client, funded_student_a1, trip_fee, amount="1000")
        assert frozen.status_code == 422 and frozen.data["code"] == "card_frozen"

    def test_amount_rules(self, parent_client, funded_student_a1, exam_fee, trip_fee, student_a2, admin_a_client):
        assert pay(parent_client, funded_student_a1, exam_fee, amount="5000").data["code"] == "fee_amount_invalid"
        assert pay(parent_client, funded_student_a1, trip_fee, amount="9000").data["code"] == "fee_amount_invalid"
        assert pay(parent_client, funded_student_a1, trip_fee, amount="2500").status_code == 201
        student_a2.class_name = "P7"
        student_a2.save()
        assert pay(admin_a_client, student_a2, exam_fee).data["code"] == "fee_not_applicable"
        exam_fee.active = False
        exam_fee.save()
        assert pay(parent_client, funded_student_a1, exam_fee).status_code == 409

    def test_admin_can_pay_and_history_filters(self, admin_a_client, parent_client, funded_student_a1, exam_fee, trip_fee):
        assert pay(admin_a_client, funded_student_a1, exam_fee).status_code == 201
        pay(parent_client, funded_student_a1, trip_fee, amount="1000")
        assert admin_a_client.get(f"/api/v1/fees/payments/?student={funded_student_a1.pk}").data["count"] == 2
        assert admin_a_client.get(f"/api/v1/fees/payments/?fee_category={exam_fee.pk}").data["count"] == 1
        assert parent_client.get("/api/v1/fees/payments/").data["count"] == 2

    def test_isolation(self, admin_b_client, other_parent, funded_student_a1, exam_fee, parent_client):
        pay(parent_client, funded_student_a1, exam_fee)
        assert pay(client_for(other_parent), funded_student_a1, exam_fee).status_code == 404
        assert pay(admin_b_client, funded_student_a1, exam_fee).status_code == 404
        assert admin_b_client.get("/api/v1/fees/payments/").data["count"] == 0
        assert admin_b_client.get("/api/v1/fee-categories/").data["count"] == 0
        assert admin_b_client.patch(f"/api/v1/fee-categories/{exam_fee.pk}/", {"name": "x"}, format="json").status_code == 404
        assert client_for(other_parent).get("/api/v1/fees/payments/").data["count"] == 0

    def test_category_validation(self, admin_a_client, parent_client):
        bad = admin_a_client.post("/api/v1/fee-categories/", {"name": "X", "amount_type": "range", "min_amount": "5", "max_amount": "1"}, format="json")
        assert bad.status_code == 400
        assert parent_client.post("/api/v1/fee-categories/", {"name": "Y", "fixed_amount": "5"}, format="json").status_code == 403

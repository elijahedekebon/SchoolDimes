from decimal import Decimal

import pytest

from conftest import assert_books_balanced, client_for
from notifications.models import NotificationEvent
from payments.models import Deposit
from payments.services import mock_confirm
from pooled_funds.models import PooledFund
from pooled_funds.services import fund_totals
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_system_wallet


@pytest.fixture
def fund(parent_client, guardian_link_a1):
    resp = parent_client.post("/api/v1/pooled-funds/", {
        "title": "P4 trip to Entebbe Zoo", "purpose": "Bus + tickets",
        "group_label": "P4", "target_amount": "20000",
    }, format="json")
    assert resp.status_code == 201, resp.data
    return PooledFund.objects.get(pk=resp.data["id"])


def contribute(client, fund, key, amount="5000", phone="0772000111"):
    return client.post(f"/api/v1/pooled-funds/{fund.pk}/contribute/", {
        "amount": amount, "channel": "momo", "payer_phone": phone, "idempotency_key": key,
    }, format="json")


@pytest.mark.django_db
class TestPooledFunds:
    def test_parent_creates_fund_for_their_childs_school(self, fund, school_a):
        assert fund.school == school_a
        assert fund.wallet.wallet_type == Wallet.WalletType.POOLED_FUND
        assert fund.wallet.student is None

    def test_parent_without_children_cannot_create(self, other_parent):
        resp = client_for(other_parent).post("/api/v1/pooled-funds/", {"title": "x"}, format="json")
        assert resp.status_code == 400 and resp.data["code"] == "school_required"

    def test_parent_cannot_target_another_school(self, parent_client, guardian_link_a1, school_b):
        resp = parent_client.post("/api/v1/pooled-funds/", {"title": "x", "school": school_b.pk}, format="json")
        assert resp.status_code == 404

    def test_contributions_only_count_when_confirmed_and_total_matches_ledger(
        self, fund, parent_client, admin_a_client, parent_user, school_a
    ):
        d1 = Deposit.objects.get(reference=contribute(parent_client, fund, "c1").data["reference"])
        d2 = Deposit.objects.get(reference=contribute(admin_a_client, fund, "c2", amount="7000").data["reference"])
        contribute(parent_client, fund, "c3", phone="0772000999")  # declined
        detail = parent_client.get(f"/api/v1/pooled-funds/{fund.pk}/").data
        assert detail["total_contributed"] == "0" and detail["contributions"] == []

        mock_confirm(d1)
        mock_confirm(d2)
        mock_confirm(d1)  # replay
        detail = parent_client.get(f"/api/v1/pooled-funds/{fund.pk}/").data
        assert Decimal(detail["total_contributed"]) == Decimal("12000")
        assert Decimal(detail["balance"]) == Decimal("12000")
        assert detail["progress_percent"] == 60.0
        assert len(detail["contributions"]) == 2
        fund.wallet.refresh_from_db()
        assert fund.wallet.cached_balance == sum(Decimal(c["amount"]) for c in detail["contributions"])
        assert LedgerEntry.objects.filter(wallet=fund.wallet, entry_type="pooled_fund_contribution").count() == 2
        assert NotificationEvent.objects.filter(user=parent_user, event_type="pooled_fund_contribution_confirmed").count() == 1
        assert_books_balanced(school_a)

    def test_only_school_admin_disburses_and_not_more_than_held(self, fund, parent_client, admin_a_client, school_a):
        mock_confirm(Deposit.objects.get(reference=contribute(parent_client, fund, "c1").data["reference"]))
        body = {"amount": "3000", "destination": "school_settlement", "description": "Bus hire deposit"}
        # creator (a parent) may close but not disburse
        assert parent_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", body, format="json").status_code == 403
        too_much = admin_a_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", {**body, "amount": "9000"}, format="json")
        assert too_much.status_code == 422 and too_much.data["code"] == "insufficient_funds"
        no_desc = admin_a_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", {**body, "description": " "}, format="json")
        assert no_desc.status_code == 400

        assert admin_a_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", body, format="json").status_code == 201
        settlement = get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
        assert settlement.cached_balance == Decimal("3000")
        totals = fund_totals(fund)
        assert totals["balance"] == Decimal("2000") and totals["total_disbursed"] == Decimal("3000")
        assert_books_balanced(school_a)

    def test_external_disbursement_and_failed_payout_reversal(self, fund, parent_client, admin_a_client, school_a):
        mock_confirm(Deposit.objects.get(reference=contribute(parent_client, fund, "c1").data["reference"]))
        ok = admin_a_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", {
            "amount": "1000", "destination": "external", "description": "Teacher gift", "phone_number": "0772111222",
        }, format="json")
        assert ok.status_code == 201 and ok.data["payout_status"] == "succeeded"
        failed = admin_a_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", {
            "amount": "1000", "destination": "external", "description": "Retry", "phone_number": "0772111998",
        }, format="json")
        assert failed.data["payout_status"] == "failed"
        assert fund_totals(fund)["balance"] == Decimal("4000")  # 5000 - 1000, failed one reversed
        assert LedgerEntry.objects.filter(wallet=fund.wallet, entry_type="reversal").count() == 1
        assert_books_balanced(school_a)

    def test_close_then_full_disbursement_marks_disbursed(self, fund, parent_client, admin_a_client, other_parent):
        mock_confirm(Deposit.objects.get(reference=contribute(parent_client, fund, "c1").data["reference"]))
        assert client_for(other_parent).post(f"/api/v1/pooled-funds/{fund.pk}/close/").status_code == 404
        assert parent_client.post(f"/api/v1/pooled-funds/{fund.pk}/close/").data["status"] == "closed"
        assert contribute(parent_client, fund, "late").data["code"] == "fund_not_open"
        admin_a_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", {
            "amount": "5000", "destination": "school_settlement", "description": "Trip paid",
        }, format="json")
        fund.refresh_from_db()
        assert fund.status == "disbursed"

    def test_tenant_isolation(self, fund, admin_b_client, other_parent):
        assert admin_b_client.get("/api/v1/pooled-funds/").data["results"] == []
        assert admin_b_client.get(f"/api/v1/pooled-funds/{fund.pk}/").status_code == 404
        assert admin_b_client.post(f"/api/v1/pooled-funds/{fund.pk}/disburse/", {}, format="json").status_code == 404
        assert client_for(other_parent).get(f"/api/v1/pooled-funds/{fund.pk}/").status_code == 404


@pytest.mark.django_db
def test_parent_with_two_children_in_one_school_needs_no_school(parent_client, guardian_link_a1, parent_user, student_a2):
    """Regression: user_school_ids() returned one id per sibling (DISTINCT +
    Student.Meta.ordering), so this parent was asked to pick a school."""
    from students.models import Guardian

    Guardian.objects.create(parent=parent_user, student=student_a2)
    assert parent_client.post("/api/v1/pooled-funds/", {"title": "Sports day"}, format="json").status_code == 201

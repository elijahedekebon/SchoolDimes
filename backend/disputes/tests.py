from decimal import Decimal

import pytest

from conftest import assert_books_balanced, client_for
from disputes.models import Dispute
from fees.models import FeeCategory
from notifications.models import NotificationEvent
from pos.services import register_device
from pos.tests import device_client, sale
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_student_wallet, get_system_wallet


@pytest.fixture
def sold(school_admin_a, school_a, funded_student_a1):
    """A synced 3,000 canteen sale on student_a1's card."""
    _, raw = register_device(school_admin_a, school=school_a, device_name="Till", device_role="canteen")
    result = device_client(raw).post("/api/v1/pos/sync/", {"transactions": [sale(funded_student_a1.cards.get(), 3000)]},
                                     format="json").data["results"][0]
    return result["transaction_id"]


def raise_(client, txn_id, reason="wrong_amount"):
    return client.post("/api/v1/disputes/", {"pos_transaction": txn_id, "reason_category": reason,
                                             "description": "Only bought one samosa"}, format="json")


@pytest.mark.django_db
class TestDisputes:
    def test_partial_then_capped_refunds(self, parent_client, admin_a_client, sold, funded_student_a1, parent_user, school_a):
        d1 = raise_(parent_client, sold)
        assert d1.status_code == 201 and d1.data["original_amount"] == "3000.00"
        assert raise_(parent_client, sold).status_code == 409  # one open dispute per transaction
        assert admin_a_client.post(f"/api/v1/disputes/{d1.data['id']}/review/").data["status"] == "under_review"
        r1 = admin_a_client.post(f"/api/v1/disputes/{d1.data['id']}/resolve/", {
            "outcome": "refund", "refund_amount": "1000", "resolution_notes": "Overcharged"}, format="json")
        assert r1.status_code == 200 and r1.data["status"] == "resolved_refunded"
        assert get_student_wallet(funded_student_a1).cached_balance == Decimal("8000")  # 10000 - 3000 + 1000
        refund = LedgerEntry.objects.filter(reference_id=f"refund:{d1.data['id']}")
        assert set(refund.values_list("direction", "entry_type")) == {("debit", "refund"), ("credit", "refund")}
        assert refund.get(direction="debit").wallet == get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
        events = NotificationEvent.objects.filter(user=parent_user, event_type="dispute_status_changed")
        assert events.count() == 2  # under_review, resolved

        d2 = raise_(parent_client, sold, reason="duplicate")
        assert d2.status_code == 201 and d2.data["refunded_total"] == "1000.00"
        too_much = admin_a_client.post(f"/api/v1/disputes/{d2.data['id']}/resolve/", {"outcome": "refund", "refund_amount": "2500"}, format="json")
        assert too_much.status_code == 422 and too_much.data["code"] == "refund_exceeds_original"
        ok = admin_a_client.post(f"/api/v1/disputes/{d2.data['id']}/resolve/", {"outcome": "refund", "refund_amount": "2000"}, format="json")
        assert ok.status_code == 200
        d3 = raise_(parent_client, sold, reason="other")
        assert admin_a_client.post(f"/api/v1/disputes/{d3.data['id']}/resolve/", {"outcome": "refund", "refund_amount": "1"}, format="json").status_code == 422
        assert_books_balanced(school_a)

    def test_deny(self, parent_client, admin_a_client, sold, parent_user):
        d = raise_(parent_client, sold).data
        resp = admin_a_client.post(f"/api/v1/disputes/{d['id']}/resolve/", {"outcome": "deny", "resolution_notes": "CCTV shows purchase"}, format="json")
        assert resp.data["status"] == "resolved_denied" and resp.data["refund_amount"] == "0.00"
        assert "CCTV" in NotificationEvent.objects.filter(event_type="dispute_status_changed").first().body
        again = admin_a_client.post(f"/api/v1/disputes/{d['id']}/resolve/", {"outcome": "deny"}, format="json")
        assert again.status_code == 409

    def test_only_school_admin_resolves(self, parent_client, sold, admin_b_client, platform_admin, school_a):
        from accounts.models import User

        d = raise_(parent_client, sold).data
        body = {"outcome": "refund", "refund_amount": "100"}
        assert parent_client.post(f"/api/v1/disputes/{d['id']}/resolve/", body, format="json").status_code == 403
        assert admin_b_client.post(f"/api/v1/disputes/{d['id']}/resolve/", body, format="json").status_code == 404
        assert client_for(platform_admin).post(f"/api/v1/disputes/{d['id']}/resolve/", body, format="json").status_code == 403
        canteen = User.objects.create_user(email="c@x.test", password="pw", role="canteen_staff", school=school_a)
        assert client_for(canteen).post(f"/api/v1/disputes/{d['id']}/resolve/", body, format="json").status_code == 404

    def test_visibility_and_who_can_raise(self, parent_client, sold, other_parent, admin_a_client, admin_b_client):
        assert raise_(client_for(other_parent), sold).status_code == 404
        raise_(parent_client, sold)
        assert parent_client.get("/api/v1/disputes/").data["count"] == 1
        assert admin_a_client.get("/api/v1/disputes/?status=open").data["count"] == 1
        assert admin_b_client.get("/api/v1/disputes/").data["count"] == 0
        assert client_for(other_parent).get("/api/v1/disputes/").data["count"] == 0

    def test_fee_payment_dispute_refunds_from_settlement(self, parent_client, admin_a_client, funded_student_a1, school_a):
        fee = FeeCategory.objects.create(school=school_a, name="Trip", fixed_amount=Decimal("4000"))
        parent_client.post("/api/v1/fees/pay/", {"student": funded_student_a1.pk, "fee_category": fee.pk}, format="json")
        entry = LedgerEntry.objects.get(entry_type="fee_payment", direction="debit")
        d = parent_client.post("/api/v1/disputes/", {"ledger_entry": entry.pk, "reason_category": "not_received"}, format="json")
        assert d.status_code == 201, d.data
        admin_a_client.post(f"/api/v1/disputes/{d.data['id']}/resolve/", {"outcome": "refund", "refund_amount": "4000"}, format="json")
        assert get_student_wallet(funded_student_a1).cached_balance == Decimal("10000")
        assert_books_balanced(school_a)

    def test_non_disputable_entries(self, parent_client, funded_student_a1):
        deposit_entry = LedgerEntry.objects.filter(wallet__student=funded_student_a1, direction="credit").first()
        resp = parent_client.post("/api/v1/disputes/", {"ledger_entry": deposit_entry.pk, "reason_category": "other"}, format="json")
        assert resp.status_code == 400 and resp.data["code"] == "not_disputable"
        assert Dispute.objects.count() == 0

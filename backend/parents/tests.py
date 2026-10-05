"""Part 4A Section J: parent-app readiness endpoints."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from conftest import client_for, fund_wallet
from wallets.services import ensure_student_wallets


def sale(device, card, amount="1500.00", key="k1", items=None):
    from pos.services import sync_batch

    return sync_batch(device, [{
        "idempotency_key": key, "card_uid": card.card_uid, "amount": amount, "pin_verified": True,
        "device_local_timestamp": "2026-10-05T10:00:00+03:00",
        "items": items or [{"description": "Chapati", "quantity": 3, "unit_price": "500.00"}],
    }])


@pytest.fixture
def device_a(db, school_admin_a, school_a):
    from pos.services import register_device

    device, _token = register_device(school_admin_a, school=school_a, device_name="Till", device_role="canteen")
    return device


@pytest.fixture
def family(db, parent_user, guardian_link_a1, student_a1):
    from cards.services import issue_card

    main, savings = ensure_student_wallets(student_a1)
    card = issue_card(student_a1, "1234", card_uid="04aabbcc")
    fund_wallet(main, "10000")
    return {"main": main, "savings": savings, "card": card}


@pytest.mark.django_db
class TestRegister:
    def test_register_creates_logged_in_parent(self, api_client):
        r = api_client.post("/api/v1/auth/register", {"email": "New@Parent.test", "password": "a-long-pass-123",
                                                      "full_name": "New Parent", "preferred_language": "lg"}, format="json")
        assert r.status_code == 201, r.data
        assert r.data["user"]["role"] == "parent" and r.data["user"]["email"] == "new@parent.test"
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.data['access']}")
        assert c.get("/api/v1/me").data["preferred_language"] == "lg"

    def test_duplicate_and_weak_password(self, api_client, parent_user):
        assert api_client.post("/api/v1/auth/register", {"email": parent_user.email, "password": "a-long-pass-123",
                                                         "full_name": "X"}, format="json").status_code == 400
        assert api_client.post("/api/v1/auth/register", {"email": "w@p.test", "password": "12345678",
                                                         "full_name": "X"}, format="json").status_code == 400

    def test_cannot_choose_role(self, api_client):
        r = api_client.post("/api/v1/auth/register", {"email": "sneaky@p.test", "password": "a-long-pass-123",
                                                      "full_name": "X", "role": "platform_admin"}, format="json")
        assert r.status_code == 201
        assert User.objects.get(email="sneaky@p.test").role == "parent"

    def test_throttled(self, api_client, settings):
        settings.AUTH_THROTTLE_RATE = "2/min"
        codes = [api_client.post("/api/v1/auth/register", {"email": f"t{i}@p.test", "password": "a-long-pass-123",
                                                           "full_name": "X"}, format="json").status_code for i in range(3)]
        assert codes == [201, 201, 429]


@pytest.mark.django_db
class TestDashboard:
    def test_one_call_has_everything(self, parent_user, family, device_a, student_a1, student_b1):
        sale(device_a, family["card"])
        r = client_for(parent_user).get("/api/v1/parent/dashboard/")
        assert r.status_code == 200
        assert [s["id"] for s in r.data["students"]] == [student_a1.pk]  # never another family's child
        s = r.data["students"][0]
        assert s["main_wallet"]["balance"] == "8500.00" and s["savings_wallet"]["balance"] == "0.00"
        assert s["card"] == {"id": family["card"].pk, "card_uid": "04aabbcc", "status": "active",
                             "updated_at": s["card"]["updated_at"]}
        first = s["recent_transactions"][0]
        assert first["entry_type"] == "pos_purchase" and first["direction"] == "debit"
        assert first["pos"]["items"][0]["description"] == "Chapati"
        assert first["dispute_target"] == {"pos_transaction": first["pos"]["transaction_id"]}
        assert "pin_hash" not in str(r.data)

    def test_non_parent_refused(self, school_admin_a):
        assert client_for(school_admin_a).get("/api/v1/parent/dashboard/").status_code == 403


@pytest.mark.django_db
class TestTransactions:
    def test_filters_items_and_scoping(self, parent_user, other_parent, school_admin_a, school_admin_b, family, device_a,
                                       student_a1):
        sale(device_a, family["card"])
        c = client_for(parent_user)
        rows = c.get(f"/api/v1/students/{student_a1.pk}/transactions/").data["results"]
        assert {r["entry_type"] for r in rows} == {"deposit", "pos_purchase"}
        debits = c.get(f"/api/v1/students/{student_a1.pk}/transactions/", {"direction": "debit"}).data
        assert debits["count"] == 1 and debits["results"][0]["pos"]["items"][0]["quantity"] == 3
        assert c.get(f"/api/v1/students/{student_a1.pk}/transactions/", {"entry_type": "deposit"}).data["count"] == 1
        assert c.get(f"/api/v1/students/{student_a1.pk}/transactions/", {"from": "2000-01-01", "to": "2000-01-02"}).data["count"] == 0
        assert client_for(school_admin_a).get(f"/api/v1/students/{student_a1.pk}/transactions/").status_code == 200
        assert client_for(other_parent).get(f"/api/v1/students/{student_a1.pk}/transactions/").status_code == 404
        assert client_for(school_admin_b).get(f"/api/v1/students/{student_a1.pk}/transactions/").status_code == 404

    def test_open_dispute_is_shown(self, parent_user, family, device_a, student_a1):
        sale(device_a, family["card"])
        c = client_for(parent_user)
        row = c.get(f"/api/v1/students/{student_a1.pk}/transactions/", {"direction": "debit"}).data["results"][0]
        d = c.post("/api/v1/disputes/", {**row["dispute_target"], "reason_category": "wrong_amount"}, format="json")
        assert d.status_code == 201, d.data
        row = c.get(f"/api/v1/students/{student_a1.pk}/transactions/", {"direction": "debit"}).data["results"][0]
        assert row["open_dispute"] == d.data["id"]


@pytest.mark.django_db
class TestSpendingControls:
    def test_school_limits_alongside_override(self, parent_user, other_parent, family, student_a1):
        from policies.models import Policy
        from policies.services import get_school_policy

        default = get_school_policy(student_a1.school_id)
        default.daily_spend_cap = Decimal("5000")
        default.save()
        Policy.objects.create(school=student_a1.school, student=student_a1, daily_spend_cap=Decimal("3000"))
        r = client_for(parent_user).get(f"/api/v1/students/{student_a1.pk}/spending-controls/")
        assert r.data["school_default"]["daily_spend_cap"] == "5000.00"
        assert r.data["override"]["daily_spend_cap"] == "3000.00"
        assert r.data["effective"]["daily_spend_cap"] == "3000.00"
        assert r.data["can_edit_override"] is True
        assert client_for(other_parent).get(f"/api/v1/students/{student_a1.pk}/spending-controls/").status_code == 404


@pytest.mark.django_db
class TestPayouts:
    def test_parent_sees_own_childs_payouts_only(self, parent_user, other_parent, family, school_admin_b):
        from django.utils import timezone

        from wallets.savings import move_to_savings, withdraw_savings

        savings = family["savings"]
        move_to_savings(family["main"].student, Decimal("2000"))
        savings.withdrawal_window_start = timezone.now() - timezone.timedelta(days=1)
        savings.withdrawal_window_end = timezone.now() + timezone.timedelta(days=1)
        savings.save(update_fields=["withdrawal_window_start", "withdrawal_window_end"])
        withdraw_savings(parent_user, savings.student, amount=Decimal("1000"), phone_number="0772000111",
                         idempotency_key="w1")
        rows = client_for(parent_user).get("/api/v1/payments/payouts/").data["results"]
        assert len(rows) == 1 and rows[0]["amount"] == "1000.00" and rows[0]["status"] in ("pending", "succeeded")
        assert client_for(other_parent).get("/api/v1/payments/payouts/").data["count"] == 0
        assert client_for(school_admin_b).get("/api/v1/payments/payouts/").data["count"] == 0


@pytest.mark.django_db
def test_contributions_received_filter(parent_user, family, student_a1, api_client):
    from payments.models import StudentTopUpLink  # noqa: F401

    link = client_for(parent_user).post("/api/v1/payments/topup-links/", {"student": student_a1.pk}, format="json").data
    api_client.post(f"/api/v1/public/topup-links/{link['token']}/deposits/", {
        "contributor": {"name": "Jjajja", "phone_number": "0701000222"}, "amount": "3000", "channel": "momo",
        "idempotency_key": "contrib-1"}, format="json")
    client_for(parent_user).post("/api/v1/payments/deposits/", {"wallet": family["main"].pk, "amount": "1000",
                                                                 "channel": "momo", "idempotency_key": "own-1"}, format="json")
    rows = client_for(parent_user).get("/api/v1/payments/deposits/", {"from_contributor": "true"}).data["results"]
    assert [r["contributor_name"] for r in rows] == ["Jjajja"]

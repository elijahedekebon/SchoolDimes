"""Part 4A: platform back-office -- onboarding, stats, audit log, unmatched webhooks."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from accounts.models import User
from conftest import assert_books_balanced, client_for
from payments.aggregator_client import MockAggregatorClient
from payments.models import Deposit, UnmatchedWebhook
from tenants.models import School

ONBOARD = {
    "name": "Mbale Hill Primary",
    "address": "Mbale",
    "branding": {"logo_url": "https://example.org/logo.png", "primary_color": "#0E7C66"},
    "supported_languages": ["en", "sw"],
    "policy": {"daily_spend_cap": "5000.00", "per_transaction_cap": "3000.00", "p2p_enabled": False},
    "settings": {"offline_spend_ceiling": "1500.00", "pin_lockout_threshold": 4},
    "admin": {"email": "head@mbalehill.test", "password": "longpassword1", "full_name": "Head Teacher"},
}


@pytest.mark.django_db
class TestOnboarding:
    def test_only_platform_admin(self, school_admin_a):
        assert client_for(school_admin_a).post("/api/v1/platform/schools/onboard/", ONBOARD, format="json").status_code == 403

    def test_onboard_creates_everything(self, platform_admin):
        from policies.models import Policy
        from wallets.models import Wallet

        r = client_for(platform_admin).post("/api/v1/platform/schools/onboard/", ONBOARD, format="json")
        assert r.status_code == 201, r.data
        school = School.objects.get(pk=r.data["school"]["id"])
        assert school.branding["primary_color"] == "#0E7C66"
        assert school.settings.offline_spend_ceiling == Decimal("1500.00")
        assert school.settings.pin_lockout_threshold == 4
        default = Policy.objects.get(school=school, student=None)
        assert default.daily_spend_cap == Decimal("5000.00") and default.p2p_enabled is False
        assert set(Wallet.objects.filter(school=school, student=None).values_list("wallet_type", flat=True)) == {
            "school_settlement", "aggregator_clearing"}
        admin = User.objects.get(email="head@mbalehill.test")
        assert admin.role == "school_admin" and admin.school == school and admin.check_password("longpassword1")
        assert "password" not in r.data["admin"]
        from core.models import AuditLog
        assert AuditLog.objects.filter(action="school.onboard", school=school).exists()

    def test_duplicate_admin_email_rolls_back(self, platform_admin, school_admin_a):
        body = {**ONBOARD, "admin": {**ONBOARD["admin"], "email": school_admin_a.email}}
        r = client_for(platform_admin).post("/api/v1/platform/schools/onboard/", body, format="json")
        assert r.status_code == 400
        assert not School.objects.filter(name="Mbale Hill Primary").exists()

    def test_new_school_takes_a_sale_using_only_endpoints(self, platform_admin):
        """A brand-new school, onboarded purely through the API, registers a
        device, issues a card, gets a (mock-confirmed) top-up and takes a sale."""
        r = client_for(platform_admin).post("/api/v1/platform/schools/onboard/", ONBOARD, format="json")
        school = School.objects.get(pk=r.data["school"]["id"])
        admin = APIClient()
        tokens = admin.post("/api/v1/auth/login", {"email": "head@mbalehill.test", "password": "longpassword1"},
                            format="json").data
        admin.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        student = admin.post("/api/v1/students/", {"name": "Okello John", "class_name": "P5"}, format="json").data
        card = admin.post("/api/v1/cards/issue/", {"student": student["id"], "pin": "2468",
                                                   "card_uid": "04:11:22:33:44:55:66"}, format="json")
        assert card.status_code == 201, card.data
        device = admin.post("/api/v1/pos/devices/register/", {"device_name": "Till 1", "device_role": "canteen"},
                            format="json")
        assert device.status_code == 201, device.data
        cat = admin.post("/api/v1/product-categories/", {"name": "Meals"}, format="json").data
        product = admin.post("/api/v1/products/", {"name": "Posho & beans", "category": cat["id"], "price": "2000"},
                             format="json").data

        # a parent registers (Section J), is linked by the admin, and tops up
        parent = User.objects.create_user(email="mum@mbalehill.test", password="longpassword1", role="parent")
        assert admin.post("/api/v1/guardians/", {"parent": parent.pk, "student": student["id"], "relationship": "mother"},
                          format="json").status_code == 201
        wallet = next(w for w in client_for(parent).get("/api/v1/wallets/").data["results"] if w["wallet_type"] == "main")
        dep = client_for(parent).post("/api/v1/payments/deposits/", {
            "wallet": wallet["id"], "amount": "10000", "channel": "momo", "payer_phone": "0772000111",
            "idempotency_key": "onboard-test-1"}, format="json").data
        deposit = Deposit.objects.get(pk=dep["id"])
        raw, headers = MockAggregatorClient.build_webhook(reference=deposit.reference, aggregator_ref=deposit.aggregator_ref,
                                                          amount=deposit.amount, success=True)
        hook = APIClient().post("/api/v1/payments/webhook/", data=raw, content_type="application/json",
                                **{f"HTTP_{k.upper().replace('-', '_')}": v for k, v in headers.items()})
        assert hook.data["status"] == "confirmed"

        pos = APIClient()
        pos.credentials(HTTP_AUTHORIZATION=f"Device {device.data['device_token']}")
        cache = pos.get("/api/v1/pos/cache/").data
        assert [c["card_uid"] for c in cache["cards"]] == ["04112233445566"]
        sale = pos.post("/api/v1/pos/purchase/", {
            "idempotency_key": "sale-1", "card_uid": "04112233445566", "amount": "2000.00", "pin": "2468",
            "items": [{"product_id": product["id"], "quantity": 1, "unit_price": "2000.00"}],
            "device_local_timestamp": "2026-10-05T10:00:00+03:00"}, format="json")
        assert sale.status_code == 201, sale.data
        assert sale.data["status"] == "applied"
        assert sale.data["balance"]["balance"] == "8000.00"
        assert_books_balanced(school)


@pytest.mark.django_db
class TestStatsAuditWebhooks:
    def test_stats_platform_only(self, platform_admin, school_admin_a, student_a1, school_b):
        r = client_for(platform_admin).get("/api/v1/platform/schools/stats/")
        row = next(s for s in r.data["results"] if s["id"] == student_a1.school_id)
        assert row["students"] == 1 and row["sales_30d_count"] == 0
        assert client_for(school_admin_a).get("/api/v1/platform/schools/stats/").status_code == 403

    def test_audit_log_lists_cross_tenant_writes(self, platform_admin, school_a, school_admin_a):
        client_for(platform_admin).patch(f"/api/v1/school-settings/?school={school_a.pk}",
                                         {"device_stale_after_hours": 12}, format="json")
        r = client_for(platform_admin).get("/api/v1/audit-logs/", {"school": school_a.pk})
        assert r.data["count"] >= 1 and r.data["results"][0]["actor_email"] == platform_admin.email
        assert client_for(school_admin_a).get("/api/v1/audit-logs/").status_code == 403

    def test_unmatched_webhooks(self, platform_admin, school_admin_a):
        hook = UnmatchedWebhook.objects.create(reference="SD-DEP-NOPE", reason="unknown_reference")
        c = client_for(platform_admin)
        assert c.get("/api/v1/payments/unmatched-webhooks/", {"reviewed": "false"}).data["count"] == 1
        assert c.post(f"/api/v1/payments/unmatched-webhooks/{hook.pk}/mark-reviewed/").data["reviewed"] is True
        assert client_for(school_admin_a).get("/api/v1/payments/unmatched-webhooks/").status_code == 403

    def test_platform_school_filter_on_support_reads(self, platform_admin, card_a1, school_b):
        c = client_for(platform_admin)
        assert c.get("/api/v1/cards/", {"school": school_b.pk}).data["count"] == 0
        assert c.get("/api/v1/cards/", {"school": card_a1.school_id}).data["count"] == 1

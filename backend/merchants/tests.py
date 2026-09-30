import uuid
from decimal import Decimal

import pytest
from django.utils import timezone

from accounts.models import User
from cards.services import issue_card
from conftest import assert_books_balanced, client_for, fund_wallet
from merchants.models import Merchant
from merchants.services import get_merchant_settlement_wallet, link_staff
from policies.models import Policy, Product, ProductCategory
from pos.models import PosTransaction
from pos.services import register_device
from pos.tests import device_client
from tenants.models import School
from wallets.services import ensure_student_wallets


@pytest.fixture
def bookshop(admin_a_client):
    resp = admin_a_client.post("/api/v1/merchants/", {"name": "Ntinda Bookshop", "category": "bookshop"}, format="json")
    assert resp.status_code == 201, resp.data
    assert resp.data["my_school_approval"] == "approved"
    return Merchant.objects.get(pk=resp.data["id"])


@pytest.fixture
def funded_b(student_b1):
    main, _ = ensure_student_wallets(student_b1)
    issue_card(student_b1, "2222")
    fund_wallet(main, "5000")
    return student_b1


def sale(card, amount, items=None):
    return {"idempotency_key": str(uuid.uuid4()), "card_uid": card.card_uid, "amount": str(amount),
            "items": items or [], "device_local_timestamp": timezone.now().isoformat()}


def merchant_device(admin, school, merchant):
    _, raw = register_device(admin, school=school, device_name="Bookshop till", device_role="merchant", merchant=merchant)
    return device_client(raw)


@pytest.mark.django_db
class TestMerchants:
    def test_merchant_device_needs_an_approved_merchant(self, admin_a_client, admin_b_client, bookshop):
        no_merchant = admin_a_client.post("/api/v1/pos/devices/register/", {"device_name": "x", "device_role": "merchant"}, format="json")
        assert no_merchant.status_code == 400
        not_approved = admin_b_client.post("/api/v1/pos/devices/register/", {
            "device_name": "x", "device_role": "merchant", "merchant": bookshop.pk}, format="json")
        assert not_approved.status_code == 400 and not_approved.data["code"] == "merchant_not_approved"
        ok = admin_a_client.post("/api/v1/pos/devices/register/", {
            "device_name": "Till", "device_role": "merchant", "merchant": bookshop.pk}, format="json")
        assert ok.status_code == 201 and ok.data["merchant"] == bookshop.pk

    def test_scope_follows_approvals_and_money_goes_to_merchant(
        self, bookshop, school_admin_a, school_a, school_b, admin_b_client, funded_student_a1, funded_b
    ):
        client = merchant_device(school_admin_a, school_a, bookshop)
        card_a, card_b = funded_student_a1.cards.get(), funded_b.cards.get()
        cache = client.get("/api/v1/pos/cache/").data
        assert [c["student_id"] for c in cache["cards"]] == [funded_student_a1.pk]
        refused = client.post("/api/v1/pos/sync/", {"transactions": [sale(card_b, 1000)]}, format="json").data
        assert refused["results"][0]["reason"] == "unknown_card"  # school B hasn't approved the merchant

        assert admin_b_client.post(f"/api/v1/merchants/{bookshop.pk}/approve/").data["status"] == "approved"
        cache = client.get("/api/v1/pos/cache/").data
        assert {c["student_id"] for c in cache["cards"]} == {funded_student_a1.pk, funded_b.pk}
        results = client.post("/api/v1/pos/sync/", {"transactions": [sale(card_a, 1200), sale(card_b, 800)]}, format="json").data
        assert [r["status"] for r in results["results"]] == ["applied", "applied"]
        assert get_merchant_settlement_wallet(bookshop, school_a.pk).cached_balance == Decimal("1200")
        assert get_merchant_settlement_wallet(bookshop, school_b.pk).cached_balance == Decimal("800")
        assert PosTransaction.objects.filter(merchant=bookshop, sync_status="applied").count() == 2
        assert PosTransaction.objects.filter(merchant=bookshop, reject_reason="unknown_card").count() == 1
        assert_books_balanced(school_a, school_b)

        admin_b_client.post(f"/api/v1/merchants/{bookshop.pk}/suspend/")
        assert [c["student_id"] for c in client.get("/api/v1/pos/cache/").data["cards"]] == [funded_student_a1.pk]

    def test_merchant_products_only(self, bookshop, school_admin_a, school_a, admin_a_client):
        cat = ProductCategory.objects.create(school=school_a, name="Stationery")
        Product.objects.create(school=school_a, name="Canteen chapati", category=cat, price=Decimal("500"))
        resp = admin_a_client.post("/api/v1/products/", {"name": "Exercise book", "category": cat.pk, "price": "1200",
                                                          "merchant": bookshop.pk}, format="json")
        assert resp.status_code == 201
        names = [p["name"] for p in merchant_device(school_admin_a, school_a, bookshop).get("/api/v1/pos/cache/").data["products"]]
        assert names == ["Exercise book"]
        _, raw = register_device(school_admin_a, school=school_a, device_name="Canteen", device_role="canteen")
        assert [p["name"] for p in device_client(raw).get("/api/v1/pos/cache/").data["products"]] == ["Canteen chapati"]

    def test_parent_can_block_merchant(self, bookshop, parent_client, school_admin_a, school_a, funded_student_a1):
        resp = parent_client.post("/api/v1/policies/", {"student": funded_student_a1.pk, "blocked_merchants": [bookshop.pk]}, format="json")
        assert resp.status_code == 201, resp.data
        client = merchant_device(school_admin_a, school_a, bookshop)
        card = funded_student_a1.cards.get()
        offline = client.post("/api/v1/pos/sync/", {"transactions": [sale(card, 500)]}, format="json").data["results"][0]
        assert offline["status"] == "applied" and offline["flags"] == ["merchant_blocked"]
        online = client.post("/api/v1/pos/purchase/", {"idempotency_key": "on1", "card_uid": card.card_uid, "amount": "500"}, format="json")
        assert online.status_code == 422 and online.data["code"] == "merchant_blocked"

    def test_statement_scoping(self, bookshop, school_admin_a, school_a, admin_a_client, admin_b_client,
                               funded_student_a1, funded_b, platform_admin):
        client_for(platform_admin).post(f"/api/v1/merchants/{bookshop.pk}/approve/", {"school": funded_b.school_id}, format="json")
        client = merchant_device(school_admin_a, school_a, bookshop)
        client.post("/api/v1/pos/sync/", {"transactions": [sale(funded_student_a1.cards.get(), 1000),
                                                            sale(funded_b.cards.get(), 700)]}, format="json")
        staff = User.objects.create_user(email="shop@x.test", password="pw123456", role=User.Role.MERCHANT_STAFF)
        link_staff(platform_admin, bookshop, staff)
        mine = client_for(staff).get(f"/api/v1/merchants/{bookshop.pk}/statement/").data
        assert mine["total_credits"] == "1700.00" and mine["entries"]["count"] == 2
        a_view = admin_a_client.get(f"/api/v1/merchants/{bookshop.pk}/statement/").data
        assert a_view["school_ids"] == [school_a.pk] and a_view["total_credits"] == "1000.00"
        b_view = admin_b_client.get(f"/api/v1/merchants/{bookshop.pk}/statement/").data
        assert b_view["total_credits"] == "700.00"
        # a school that never approved the merchant sees nothing of others
        c_school = School.objects.create(name="Gulu Demo")
        c_admin = User.objects.create_user(email="c@x.test", password="pw", role="school_admin", school=c_school)
        c_view = client_for(c_admin).get(f"/api/v1/merchants/{bookshop.pk}/statement/").data
        assert c_view["total_credits"] == "0.00" and c_view["entries"]["count"] == 0
        assert client_for(c_admin).get(f"/api/v1/merchants/{bookshop.pk}/").data["approved_school_ids"] == []
        other = User.objects.create_user(email="o@x.test", password="pw", role=User.Role.MERCHANT_STAFF)
        assert client_for(other).get(f"/api/v1/merchants/{bookshop.pk}/statement/").status_code == 404

    def test_only_school_admins_create_and_approve(self, parent_client, bookshop):
        assert parent_client.post("/api/v1/merchants/", {"name": "x"}, format="json").status_code == 403
        assert parent_client.post(f"/api/v1/merchants/{bookshop.pk}/approve/").status_code in (403, 404)

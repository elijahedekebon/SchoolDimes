import uuid
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from django.db.models import Sum

from conftest import client_for
from fees.models import FeeCategory
from policies.models import Product, ProductCategory
from pos.services import register_device
from pos.tests import device_client
from wallets.models import LedgerEntry

KAMPALA = ZoneInfo("Africa/Kampala")


@pytest.fixture
def sales(school_admin_a, school_a, funded_student_a1):
    meals = ProductCategory.objects.create(school=school_a, name="Meals")
    sugary = ProductCategory.objects.create(school=school_a, name="Sugary drinks", is_unhealthy=True)
    rice = Product.objects.create(school=school_a, name="Rice", category=meals, price=Decimal("3000"))
    soda = Product.objects.create(school=school_a, name="Soda", category=sugary, price=Decimal("1000"))
    _, raw = register_device(school_admin_a, school=school_a, device_name="Till 1", device_role="canteen")
    card = funded_student_a1.cards.get()

    def sale(hour, items, day=15):
        amount = sum(Decimal(i["unit_price"]) * i["quantity"] for i in items)
        return {"idempotency_key": str(uuid.uuid4()), "card_uid": card.card_uid, "amount": str(amount), "items": items,
                "device_local_timestamp": datetime(2026, 9, day, hour, 10, tzinfo=KAMPALA).isoformat()}

    line = lambda p, q=1: {"product_id": p.pk, "quantity": q, "unit_price": str(p.price)}  # noqa: E731
    device_client(raw).post("/api/v1/pos/sync/", {"transactions": [
        sale(10, [line(soda, 2)]), sale(13, [line(rice), line(soda)]), sale(13, [line(soda)], day=16),
    ]}, format="json")
    return {"rice": rice, "soda": soda}


Q = "from=2026-09-01&to=2026-09-30"


@pytest.mark.django_db
class TestAnalytics:
    def test_sales_summary_matches_ledger(self, admin_a_client, sales, school_a):
        data = admin_a_client.get(f"/api/v1/analytics/sales-summary/?{Q}").data
        assert data["totals"]["transactions"] == 3 and data["totals"]["gross_amount"] == "7000.00"
        ledger = LedgerEntry.objects.filter(school=school_a, entry_type="pos_purchase", direction="debit",
                                            reference_id__startswith="pos:").aggregate(s=Sum("amount"))["s"]
        assert Decimal(data["totals"]["collected_amount"]) == ledger
        assert [d["date"] for d in data["by_day"]] == ["2026-09-15", "2026-09-16"]
        assert data["by_device"][0]["device_name"] == "Till 1"
        assert data["by_merchant"][0]["merchant_name"] == "School canteen"

    def test_best_sellers_peak_hours_categories(self, admin_a_client, sales):
        best = admin_a_client.get(f"/api/v1/analytics/best-sellers/?{Q}").data["results"]
        assert best[0]["name"] == "Soda" and best[0]["quantity"] == 4
        hours = admin_a_client.get(f"/api/v1/analytics/peak-hours/?{Q}").data["results"]
        assert len(hours) == 24 and hours[13]["transactions"] == 2 and hours[10]["transactions"] == 1
        cats = admin_a_client.get(f"/api/v1/analytics/category-breakdown/?{Q}").data
        assert cats["unhealthy_revenue"] == "4000.00" and cats["unhealthy_share_percent"] == pytest.approx(57.1)

    def test_student_spending(self, parent_client, admin_a_client, sales, funded_student_a1, other_parent, platform_admin, school_a):
        fee = FeeCategory.objects.create(school=school_a, name="Exam", fixed_amount=Decimal("1000"))
        parent_client.post("/api/v1/fees/pay/", {"student": funded_student_a1.pk, "fee_category": fee.pk}, format="json")
        from datetime import timedelta

        from django.utils import timezone

        today = timezone.now().astimezone(KAMPALA).date()  # ledger rows are stamped "now"
        url = f"/api/v1/analytics/students/{funded_student_a1.pk}/spending/?from={today - timedelta(days=300)}&to={today}"
        data = parent_client.get(url).data
        assert data["purchases_total"] == "7000.00" and data["fees_total"] == "1000.00" and data["topups_total"] == "10000.00"
        assert data["top_items"][0]["name"] == "Soda"
        assert admin_a_client.get(url).status_code == 200
        assert client_for(other_parent).get(url).status_code == 404
        assert client_for(platform_admin).get(url).status_code == 404

    def test_reconciliation(self, admin_a_client, sales, school_a):
        from django.utils import timezone

        today = timezone.now().astimezone(KAMPALA).date().isoformat()
        data = admin_a_client.get(f"/api/v1/analytics/reconciliation/?date={today}").data
        till = data["devices"][0]
        assert till["transactions"] == 3 and till["matches"] is True and till["collected_amount"] == "7000.00"
        assert data["books_balanced"] is True and data["books_total"] == "0.00"
        assert data["system_wallets"]["school_settlement"] == "7000.00"
        assert data["deposits"]["matches"] and data["fee_payments"]["matches"]

    def test_tenant_isolation_and_platform_cross_school(self, admin_b_client, parent_client, platform_admin, sales, school_a, school_b):
        assert admin_b_client.get(f"/api/v1/analytics/sales-summary/?{Q}").data["totals"]["transactions"] == 0
        assert admin_b_client.get(f"/api/v1/analytics/best-sellers/?{Q}").data["results"] == []
        assert parent_client.get(f"/api/v1/analytics/sales-summary/?{Q}").status_code == 403
        cross = client_for(platform_admin).get(f"/api/v1/analytics/sales-summary/?{Q}").data
        assert {r["school_id"] for r in cross["by_school"]} == {school_a.pk}
        assert len(client_for(platform_admin).get("/api/v1/analytics/reconciliation/").data["schools"]) == 2

from decimal import Decimal

import pytest
from django.db import transaction

from conftest import client_for
from core.audit import AuditLog
from policies.models import Policy, Product, ProductCategory
from policies.services import get_effective_policy, get_school_policy
from wallets.models import LedgerEntry, Wallet
from wallets.services import (
    DebitContext,
    DebitKind,
    authorize_debit,
    get_student_wallet,
    get_system_wallet,
    post_transfer,
)


@pytest.fixture
def catalog(school_a):
    snacks = ProductCategory.objects.create(school=school_a, name="Snacks")
    sugary = ProductCategory.objects.create(school=school_a, name="Sugary drinks", is_unhealthy=True)
    meals = ProductCategory.objects.create(school=school_a, name="Meals")
    soda = Product.objects.create(school=school_a, name="Soda", category=sugary, price=Decimal("1500"))
    chips = Product.objects.create(school=school_a, name="Chips", category=snacks, price=Decimal("1000"))
    rice = Product.objects.create(school=school_a, name="Rice & beans", category=meals, price=Decimal("3000"))
    return {"snacks": snacks, "sugary": sugary, "meals": meals, "soda": soda, "chips": chips, "rice": rice}


def decide(wallet, amount, **ctx):
    with transaction.atomic():
        return authorize_debit(wallet, Decimal(amount), DebitContext(kind=ctx.pop("kind", DebitKind.PURCHASE), **ctx))


def item(product):
    return {"product_id": product.pk, "category_id": product.category_id}


@pytest.mark.django_db
class TestResolution:
    def test_override_only_tightens(self, school_a, student_a1, catalog):
        school = get_school_policy(school_a)
        school.daily_spend_cap = Decimal("5000")
        school.per_transaction_cap = Decimal("3000")
        school.save()
        school.blocked_categories.add(catalog["sugary"])
        override = Policy.objects.create(school=school_a, student=student_a1,
                                         daily_spend_cap=Decimal("9000"), per_transaction_cap=Decimal("2000"),
                                         p2p_enabled=True)
        override.blocked_items.add(catalog["chips"])
        eff = get_effective_policy(student_a1)
        assert eff.daily_spend_cap == Decimal("5000")      # can't loosen
        assert eff.per_transaction_cap == Decimal("2000")  # can tighten
        assert eff.blocked_category_ids == {catalog["sugary"].pk}
        assert eff.blocked_product_ids == {catalog["chips"].pk}
        school.p2p_enabled = False
        school.save()
        assert get_effective_policy(student_a1).p2p_enabled is False

    def test_allow_lists_intersect(self, school_a, student_a1, catalog):
        school = get_school_policy(school_a)
        school.allowed_categories.add(catalog["meals"], catalog["snacks"])
        override = Policy.objects.create(school=school_a, student=student_a1)
        override.allowed_categories.add(catalog["meals"])
        assert get_effective_policy(student_a1).allowed_category_ids == {catalog["meals"].pk}

    def test_no_policy_means_no_limits(self, student_a1):
        eff = get_effective_policy(student_a1)
        assert eff.daily_spend_cap is None and eff.p2p_enabled is True and eff.allowed_category_ids is None
        assert eff.low_balance_threshold == Decimal("2000")


@pytest.mark.django_db
class TestAuthorizeDebit:
    def test_caps_categories_items(self, funded_student_a1, school_a, catalog):
        wallet = get_student_wallet(funded_student_a1)
        school = get_school_policy(school_a)
        school.daily_spend_cap = Decimal("4000")
        school.per_transaction_cap = Decimal("3500")
        school.save()
        school.blocked_categories.add(catalog["sugary"])
        override = Policy.objects.create(school=school_a, student=funded_student_a1)
        override.blocked_items.add(catalog["chips"])

        assert decide(wallet, "3000", items=[item(catalog["rice"])]).allowed
        assert decide(wallet, "3600").code == "per_transaction_cap_exceeded"
        assert decide(wallet, "1500", items=[item(catalog["soda"])]).code == "category_blocked"
        assert decide(wallet, "1000", items=[item(catalog["chips"])]).code == "item_blocked"
        assert decide(wallet, "20000").violations[:1] == ["insufficient_funds"]
        # spend 3000 today, then 1500 more breaks the 4000 daily cap
        post_transfer(debit_wallet=wallet, credit_wallet=get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT),
                      amount=Decimal("3000"), entry_type=LedgerEntry.EntryType.POS_PURCHASE, reference_id="t:1")
        assert decide(wallet, "1500").code == "daily_cap_exceeded"
        assert decide(wallet, "1000").allowed

    def test_weekly_cap_and_fee_exemption(self, funded_student_a1, school_a):
        wallet = get_student_wallet(funded_student_a1)
        school = get_school_policy(school_a)
        school.weekly_spend_cap = Decimal("1000")
        school.save()
        assert decide(wallet, "1500").code == "weekly_cap_exceeded"
        assert decide(wallet, "1500", kind=DebitKind.FEE_PAYMENT).allowed

    def test_frozen_card_blocks_every_debit(self, funded_student_a1):
        wallet = get_student_wallet(funded_student_a1)
        card = funded_student_a1.cards.get()
        card.status = "frozen"
        card.save()
        for kind in (DebitKind.PURCHASE, DebitKind.P2P, DebitKind.FEE_PAYMENT, DebitKind.SAVINGS_MOVE):
            assert decide(wallet, "10", kind=kind).code == "card_frozen"
        assert decide(wallet, "10", card=card).code == "card_frozen"

    def test_system_wallets_never_spendable(self, school_a):
        assert decide(get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT), "1").code == "wallet_not_spendable"


@pytest.mark.django_db
class TestPolicyEndpoints:
    def test_parent_can_tighten_but_not_loosen(self, parent_client, student_a1, guardian_link_a1, school_a, catalog):
        school = get_school_policy(school_a)
        school.daily_spend_cap = Decimal("5000")
        school.save()
        loosen = parent_client.post("/api/v1/policies/", {"student": student_a1.pk, "daily_spend_cap": "8000"}, format="json")
        assert loosen.status_code == 400 and loosen.data["code"] == "policy_cannot_loosen"
        ok = parent_client.post("/api/v1/policies/", {
            "student": student_a1.pk, "daily_spend_cap": "2000", "blocked_categories": [catalog["snacks"].pk],
        }, format="json")
        assert ok.status_code == 201, ok.data
        resp = parent_client.patch(f"/api/v1/policies/{ok.data['id']}/", {"daily_spend_cap": "6000"}, format="json")
        assert resp.status_code == 400
        eff = parent_client.get(f"/api/v1/students/{student_a1.pk}/effective-policy/").data
        assert eff["daily_spend_cap"] == "2000.00" and eff["blocked_category_ids"] == [catalog["snacks"].pk]

    def test_parent_cannot_edit_school_default_or_other_children(self, parent_client, guardian_link_a1, student_a2, school_a):
        default = get_school_policy(school_a)
        assert parent_client.patch(f"/api/v1/policies/{default.pk}/", {"daily_spend_cap": "1"}, format="json").status_code == 403
        assert parent_client.post("/api/v1/policies/", {"student": student_a2.pk, "daily_spend_cap": "1"}, format="json").status_code == 403

    def test_admin_manages_default_catalog_and_isolation(self, admin_a_client, admin_b_client, school_a):
        cat = admin_a_client.post("/api/v1/product-categories/", {"name": "Snacks", "is_unhealthy": True}, format="json")
        assert cat.status_code == 201 and cat.data["school"] == school_a.pk
        prod = admin_a_client.post("/api/v1/products/", {"name": "Mandazi", "category": cat.data["id"], "price": "500"}, format="json")
        assert prod.status_code == 201
        # school B can neither see nor use school A's catalog
        assert admin_b_client.get("/api/v1/products/").data["results"] == []
        assert admin_b_client.patch(f"/api/v1/products/{prod.data['id']}/", {"price": "1"}, format="json").status_code == 404
        bad = admin_b_client.post("/api/v1/products/", {"name": "x", "category": cat.data["id"], "price": "5"}, format="json")
        assert bad.status_code == 400 and bad.data["code"] == "category_invalid"
        default = admin_a_client.get("/api/v1/policies/").data["results"][0]
        resp = admin_a_client.patch(f"/api/v1/policies/{default['id']}/", {"daily_spend_cap": "5000", "blocked_categories": [cat.data["id"]]}, format="json")
        assert resp.status_code == 200
        assert admin_b_client.patch(f"/api/v1/policies/{default['id']}/", {"daily_spend_cap": "1"}, format="json").status_code == 404

    def test_platform_admin_writes_are_audited(self, platform_admin, school_a):
        resp = client_for(platform_admin).post("/api/v1/product-categories/", {"name": "Stationery", "school": school_a.pk}, format="json")
        assert resp.status_code == 201
        assert AuditLog.objects.filter(action="productcategory.create", school=school_a).exists()

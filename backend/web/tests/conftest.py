"""Shared fixtures for the web tests (Django test client, session auth)."""
import pytest
from django.test import Client

from accounts.models import User

HX = {"HTTP_HX_REQUEST": "true"}


def hx(target=None):
    headers = dict(HX)
    if target:
        headers["HTTP_HX_TARGET"] = target
    return headers


def web_client(user=None, csrf=False):
    c = Client(enforce_csrf_checks=csrf)
    if user is not None:
        c.force_login(user)
    return c


@pytest.fixture
def admin_a_web(school_admin_a):
    return web_client(school_admin_a)


@pytest.fixture
def admin_b_web(school_admin_b):
    return web_client(school_admin_b)


@pytest.fixture
def platform_web(platform_admin):
    return web_client(platform_admin)


@pytest.fixture
def canteen_staff_a(db, school_a):
    return User.objects.create_user(email="canteen-a@schooldimes.test", password="pw123456",
                                    role=User.Role.CANTEEN_STAFF, school=school_a)


@pytest.fixture
def merchant_staff(db):
    return User.objects.create_user(email="merchant@schooldimes.test", password="pw123456",
                                    role=User.Role.MERCHANT_STAFF)


@pytest.fixture
def student_login_a1(db, school_admin_a, student_a1):
    from students.portal import create_portal_account

    return create_portal_account(school_admin_a, student_a1, email="amina@portal.test", password="pw123456").user


def sale(card, amount, items=None, minutes_ago=5):
    import uuid
    from datetime import timedelta

    from django.utils import timezone

    return {"idempotency_key": str(uuid.uuid4()), "card_uid": card.card_uid, "amount": str(amount),
            "items": items or [], "device_local_timestamp": (timezone.now() - timedelta(minutes=minutes_ago)).isoformat()}


@pytest.fixture
def pos_a(db, school_admin_a, school_a, funded_student_a1):
    """School A: a canteen device, a product, one normal sale (with an item)
    and one offline shortfall waiting for review."""
    from decimal import Decimal

    from policies.models import Product, ProductCategory
    from pos.services import register_device, sync_batch

    device, token = register_device(school_admin_a, school=school_a, device_name="Canteen 1", device_role="canteen")
    cat = ProductCategory.objects.create(school=school_a, name="Meals")
    rice = Product.objects.create(school=school_a, name="Rice", category=cat, price=Decimal("3000"))
    card = funded_student_a1.cards.get()
    ok = sync_batch(device, [sale(card, 3000, [{"product_id": rice.pk, "quantity": 1, "unit_price": "3000"}])], [])
    short = sync_batch(device, [sale(card, 9000)], [])  # 7,000 left -> 2,000 short
    return {"device": device, "token": token, "card": card, "student": funded_student_a1, "product": rice,
            "category": cat, "sale_id": ok["results"][0]["transaction_id"],
            "shortfall_id": short["results"][0]["transaction_id"]}


@pytest.fixture
def pos_b(db, school_admin_b, school_b, student_b1):
    """School B: its own device and sale (for tenant-isolation checks)."""
    from conftest import fund_wallet
    from cards.services import issue_card
    from pos.services import register_device, sync_batch
    from wallets.services import ensure_student_wallets

    main, _ = ensure_student_wallets(student_b1)
    fund_wallet(main, "5000")
    card = issue_card(student_b1, "1234")
    device, token = register_device(school_admin_b, school=school_b, device_name="B till", device_role="canteen")
    r = sync_batch(device, [sale(card, 6000)], [])
    return {"device": device, "card": card, "student": student_b1, "shortfall_id": r["results"][0]["transaction_id"]}

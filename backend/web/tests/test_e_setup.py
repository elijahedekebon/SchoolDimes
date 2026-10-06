"""Section E: devices (token once + QR), merchants, products, policy & settings, staff."""
import json

import pytest

from accounts.models import User
from merchants.models import Merchant, MerchantApproval
from policies.models import Policy, Product, ProductCategory
from pos.models import Device
from tenants.services import get_school_settings
from web.core.qr import provisioning_payload

from .conftest import hx

pytestmark = pytest.mark.django_db


def test_register_device_shows_token_once_with_qr(admin_a_web, school_a):
    r = admin_a_web.post("/school/devices/register", {"device_name": "Till 9", "device_role": "canteen"}, **hx())
    body = r.content.decode()
    device = Device.objects.get(device_name="Till 9")
    assert device.school == school_a and r["Cache-Control"] == "no-store"
    token = body.split('data-testid="device-token"')[1].split(">")[1].split("<")[0].strip()
    assert len(token) > 30 and token.startswith(device.token_prefix)
    assert "<svg" in body and "Shown only once" in body
    # never again: not on the list, not stored readable
    listing = admin_a_web.get("/school/devices").content.decode()
    assert "Till 9" in listing and token not in listing
    assert token not in json.dumps(list(Device.objects.values()), default=str)
    # the token authenticates the device
    from rest_framework.test import APIClient

    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Device {token}")
    assert c.get("/api/v1/pos/device/").status_code == 200


def test_qr_payload_format_and_redraw(admin_a_web):
    assert provisioning_payload("http://192.168.1.20:8000/", "tok") == (
        '{"type":"schooldimes_device","v":1,"api_base_url":"http://192.168.1.20:8000","device_token":"tok"}')
    r = admin_a_web.post("/school/devices/qr", {"api_base_url": "http://10.0.0.2:8000", "token": "abc"}, **hx())
    assert "<svg" in r.content.decode() and r["Cache-Control"] == "no-store"


def test_merchant_device_requires_merchant(admin_a_web):
    body = admin_a_web.post("/school/devices/register", {"device_name": "M", "device_role": "merchant"}, **hx())
    assert "field-error" in body.content.decode() and not Device.objects.filter(device_name="M").exists()


def test_rotate_and_revoke(admin_a_web, admin_b_web, pos_a):
    d = pos_a["device"]
    assert admin_b_web.get(f"/school/devices/{d.pk}/revoke", **hx()).status_code == 404
    body = admin_a_web.post(f"/school/devices/{d.pk}/rotate-token", **hx()).content.decode()
    assert 'data-testid="device-token"' in body
    admin_a_web.post(f"/school/devices/{d.pk}/revoke", **hx())
    d.refresh_from_db()
    assert d.status == "revoked"


def test_devices_stale_highlight(admin_a_web, pos_a):
    from datetime import timedelta

    from django.utils import timezone

    Device.objects.filter(pk=pos_a["device"].pk).update(last_sync_at=timezone.now() - timedelta(hours=48))
    body = admin_a_web.get("/school/devices", {"stale": "true"}, **hx("devices_table")).content.decode()
    assert "Canteen 1" in body and ">stale<" in body


def test_merchants_create_approve_suspend_statement(admin_a_web, admin_b_web, school_a):
    admin_a_web.post("/school/merchants/new", {"name": "Mama Shop", "category": "food"}, **hx())
    m = Merchant.objects.get(name="Mama Shop")
    assert MerchantApproval.objects.get(merchant=m, school=school_a).status == "approved"
    body = admin_a_web.get("/school/merchants").content.decode()
    assert "Mama Shop" in body and "Statement" in body
    admin_a_web.post(f"/school/merchants/{m.pk}/suspend", **hx())
    assert MerchantApproval.objects.get(merchant=m, school=school_a).status == "suspended"
    admin_a_web.post(f"/school/merchants/{m.pk}/approve", **hx())
    r = admin_a_web.get(f"/school/merchants/{m.pk}/statement", **hx())
    assert r.status_code == 200 and "Settlement balance" in r.content.decode() or "Credits" in r.content.decode()


def test_categories_and_products_crud(admin_a_web, admin_b_web, school_a):
    admin_a_web.post("/school/products/categories/new", {"name": "Sweets", "is_unhealthy": "1", "active": "1"}, **hx())
    cat = ProductCategory.objects.get(name="Sweets")
    assert cat.is_unhealthy and cat.school == school_a
    body = admin_a_web.post("/school/products/new", {"name": "Lolly", "category": cat.pk, "price": "-5", "active": "1"}, **hx())
    assert "Enter a positive amount" in body.content.decode()
    admin_a_web.post("/school/products/new", {"name": "Lolly", "category": cat.pk, "price": "500", "active": "1"}, **hx())
    p = Product.objects.get(name="Lolly")
    admin_a_web.post(f"/school/products/{p.pk}/edit", {"name": "Lolly", "category": cat.pk, "price": "600"}, **hx())
    p.refresh_from_db()
    assert str(p.price) == "600.00" and p.active is False
    assert admin_b_web.get(f"/school/products/{p.pk}/edit", **hx()).status_code == 404
    admin_a_web.post(f"/school/products/{p.pk}/delete", **hx())
    assert not Product.objects.filter(pk=p.pk).exists()


def test_policy_default_settings_and_overrides(admin_a_web, school_a, student_a1, parent_user, guardian_link_a1):
    from policies.services import get_school_policy

    r = admin_a_web.post("/school/policy/default", {"daily_spend_cap": "abc"}, **hx())
    assert "field-error" in r.content.decode()
    r = admin_a_web.post("/school/policy/default", {"daily_spend_cap": "4000", "weekly_spend_cap": "",
                                                    "p2p_enabled": "1"}, **hx())
    assert "Saved" in r["HX-Trigger"]
    pol = get_school_policy(school_a.pk)
    assert str(pol.daily_spend_cap) == "4000.00" and pol.weekly_spend_cap is None and pol.p2p_enabled
    admin_a_web.post("/school/policy/settings", {"offline_spend_ceiling": "1500", "pin_lockout_threshold": "3",
                                                 "device_stale_after_hours": "12"}, **hx())
    st = get_school_settings(school_a.pk)
    assert (str(st.offline_spend_ceiling), st.pin_lockout_threshold, st.attendance_notify_guardians) == ("1500.00", 3, False)
    override = Policy.objects.create(school=school_a, student=student_a1, daily_spend_cap="1000", updated_by=parent_user)
    body = admin_a_web.get("/school/policy").content.decode()
    assert student_a1.name in body and "badge-filled c-grape" in body  # set by a parent
    admin_a_web.post(f"/school/policy/overrides/{override.pk}/remove", **hx())
    assert not Policy.objects.filter(pk=override.pk).exists()


def test_staff_accounts(admin_a_web, admin_b_web, school_a, school_admin_a):
    body = admin_a_web.post("/school/staff/new", {"role": "canteen_staff", "email": "c@x.test", "password": "short"}, **hx())
    assert "At least 8 characters" in body.content.decode()
    admin_a_web.post("/school/staff/new", {"role": "canteen_staff", "email": "c@x.test", "password": "longenough",
                                           "full_name": "Cook"}, **hx())
    u = User.objects.get(email="c@x.test")
    assert u.role == "canteen_staff" and u.school == school_a
    assert admin_b_web.get(f"/school/staff/{u.pk}/toggle", **hx()).status_code == 404
    admin_a_web.post(f"/school/staff/{u.pk}/toggle", **hx())
    u.refresh_from_db()
    assert u.is_active is False
    admin_a_web.post(f"/school/staff/{u.pk}/set-password", {"password": "anotherlong"}, **hx())
    u.refresh_from_db()
    assert u.check_password("anotherlong")
    body = admin_a_web.post(f"/school/staff/{school_admin_a.pk}/toggle", **hx()).content.decode()
    assert "cannot_deactivate_self" in body


def test_e_pages_render(admin_a_web, pos_a):
    for url in ("/school/devices", "/school/merchants", "/school/products", "/school/policy", "/school/staff"):
        r = admin_a_web.get(url)
        assert r.status_code == 200 and 'data-testid="error-alert"' not in r.content.decode(), url

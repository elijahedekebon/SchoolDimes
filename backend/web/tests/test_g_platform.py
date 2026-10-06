"""Section G: platform back-office, role protection, onboarding end to end."""
import pytest

from accounts.models import User
from content.models import FinancialLiteracyTip
from core.models import AuditLog
from tenants.models import School, SchoolReferral

from .conftest import hx, web_client

pytestmark = pytest.mark.django_db

PLATFORM_PAGES = ("/platform", "/platform/onboard", "/platform/referrals", "/platform/support",
                  "/platform/payment-issues", "/platform/audit-log", "/platform/tips")


def test_platform_pages_render(platform_web, pos_a, school_a):
    for url in PLATFORM_PAGES + (f"/platform/support?school={school_a.pk}",):
        r = platform_web.get(url)
        assert r.status_code == 200 and 'data-testid="error-alert"' not in r.content.decode(), url
    body = platform_web.get(f"/platform/support?school={school_a.pk}").content.decode()
    assert "Canteen 1" in body and pos_a["student"].name in body
    assert "SchoolDimes back-office" in body


def test_role_protection(school_admin_a, platform_admin, parent_user, canteen_staff_a, merchant_staff, student_login_a1):
    assert web_client(school_admin_a).get("/platform")["Location"] == "/school"
    assert web_client(school_admin_a).get("/platform/onboard")["Location"] == "/school"
    assert web_client(platform_admin).get("/school/students")["Location"] == "/platform"
    assert web_client(student_login_a1).get("/school")["Location"] == "/student"
    assert web_client(student_login_a1).get("/platform")["Location"] == "/student"
    for user in (parent_user, canteen_staff_a, merchant_staff):
        for url in ("/school", "/platform", "/school/cards"):
            assert web_client(user).get(url)["Location"] == "/login?refused=1", (user.role, url)
    assert web_client().get("/platform/audit-log")["Location"] == "/login?next=/platform/audit-log"


def test_referrals_and_audit_log(platform_web, school_a, school_b):
    platform_web.post("/platform/referrals/new", {"referring_school": school_a.pk, "referred_school": school_b.pk}, **hx())
    ref = SchoolReferral.objects.get(referring_school=school_a)
    body = platform_web.get("/platform/referrals").content.decode()
    assert school_a.name in body and "Apply reward" in body
    platform_web.post(f"/platform/referrals/{ref.pk}/apply", **hx())
    ref.refresh_from_db()
    assert ref.status == "applied" and ref.reward_applied
    AuditLog.objects.create(actor_role="platform_admin", school=school_a, action="card.reset_pin", details={"x": 1})
    body = platform_web.get("/platform/audit-log", {"action": "card."}, **hx("audit_table")).content.decode()
    assert "card.reset_pin" in body


def test_unmatched_webhook_mark_reviewed(platform_web):
    from payments.models import UnmatchedWebhook

    hook = UnmatchedWebhook.objects.create(reference="REF1", reason="unknown_reference", payload={"a": 1})
    assert "REF1" in platform_web.get("/platform/payment-issues").content.decode()
    platform_web.post(f"/platform/payment-issues/webhooks/{hook.pk}/mark-reviewed", **hx())
    hook.refresh_from_db()
    assert hook.reviewed and AuditLog.objects.filter(action="unmatched_webhook.reviewed").exists()


def test_platform_tips_are_global(platform_web, school_a):
    FinancialLiteracyTip.objects.create(school=school_a, title="School tip", body="b", language="en")
    platform_web.post("/platform/tips/new", {"title": "Global tip", "body": "Save", "language": "sw"}, **hx())
    assert FinancialLiteracyTip.objects.get(title="Global tip").school is None
    body = platform_web.get("/platform/tips").content.decode()
    assert "Global tip" in body and "School tip" not in body


def test_onboarded_school_can_register_device_issue_card_and_sell(platform_web, platform_admin):
    """A brand-new school created only through the back-office pages."""
    from decimal import Decimal

    from rest_framework.test import APIClient

    from cards.models import Card
    from conftest import fund_wallet
    from pos.services import sync_batch  # noqa: F401  (the API is used below)
    from wallets.models import Wallet

    from .conftest import sale

    r = platform_web.post("/platform/onboard", {
        "name": "Mbale Hill School", "supported_languages": ["en", "lg"], "primary_color": "#0E7C66",
        "daily_spend_cap": "", "low_balance_threshold": "2000", "p2p_enabled": "1",
        "offline_spend_ceiling": "2000", "pin_lockout_threshold": "5",
        "email": "head@mbale.test", "password": "longpassword1", "full_name": "Head",
    })
    assert "Mbale Hill School is ready" in r.content.decode()
    school = School.objects.get(name="Mbale Hill School")
    assert Wallet.objects.filter(school=school, wallet_type__in=["school_settlement", "aggregator_clearing"]).count() == 2
    assert AuditLog.objects.filter(action="school.onboard", school=school).exists()

    admin = web_client()
    assert admin.post("/login", {"email": "head@mbale.test", "password": "longpassword1"})["Location"] == "/school"
    assert "Mbale Hill School" in admin.get("/school").content.decode()

    admin.post("/school/students/new", {"name": "Ann Akello", "class_name": "P5"}, **hx())
    student = school.students.get(name="Ann Akello")
    admin.post("/school/cards/issue", {"student": student.pk, "card_uid": "04:11:22:33", "pin": "1234", "pin2": "1234"}, **hx())
    card = Card.objects.get(card_uid="04112233")
    body = admin.post("/school/devices/register", {"device_name": "Mbale till", "device_role": "canteen"}, **hx()).content.decode()
    token = body.split('data-testid="device-token"')[1].split(">")[1].split("<")[0].strip()

    fund_wallet(Wallet.objects.get(student=student, wallet_type="main"), "5000")
    pos = APIClient()
    pos.credentials(HTTP_AUTHORIZATION=f"Device {token}")
    resp = pos.post("/api/v1/pos/sync/", {"transactions": [sale(card, 1500)], "pin_failures": []}, format="json")
    assert resp.status_code == 200 and resp.data["results"][0]["status"] == "applied"
    assert Wallet.objects.get(student=student, wallet_type="main").cached_balance == Decimal("3500")
    assert User.objects.get(email="head@mbale.test").school == school


def test_onboard_errors_come_back_on_the_review_step(platform_web, school_admin_a):
    body = platform_web.post("/platform/onboard", {"name": "X", "supported_languages": ["en"],
                                                   "offline_spend_ceiling": "2000", "email": school_admin_a.email,
                                                   "password": "longpassword1"}).content.decode()
    assert 'data-start="4"' in body and "An account with this email already exists." in body

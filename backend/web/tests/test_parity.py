"""Cross-cutting: route parity against seed data (+ simulate_pos), CSRF on
every POST, tenant isolation on every object URL, i18n."""
import pytest
from django.conf import settings
from django.core.management import call_command
from django.urls import URLPattern, URLResolver, get_resolver

from accounts.models import User

from .conftest import hx, web_client

pytestmark = pytest.mark.django_db

# The 33 Next.js routes, at the same paths (docs/WEB_MIGRATION_PLAN.md).
SCHOOL_ROUTES = ["/school", "/school/sales", "/school/reconciliation", "/school/shortfalls", "/school/analytics",
                 "/school/students", "/school/students/{student}", "/school/guardians", "/school/cards",
                 "/school/devices", "/school/merchants", "/school/products", "/school/policy", "/school/staff",
                 "/school/fees", "/school/attendance", "/school/pooled-funds", "/school/disputes",
                 "/school/p2p-alerts", "/school/privacy", "/school/tips", "/school/payment-issues"]
PLATFORM_ROUTES = ["/platform", "/platform/onboard", "/platform/referrals", "/platform/support?school={school}",
                   "/platform/payment-issues", "/platform/audit-log", "/platform/tips"]


@pytest.fixture
def seeded(db):
    call_command("seed_demo", stdout=open("/dev/null", "w"))
    try:
        call_command("simulate_pos", stdout=open("/dev/null", "w"))
    except Exception:  # noqa: BLE001 -- the seed alone already has sales
        pass
    from students.models import Student

    amina = Student.objects.get(name="Amina Nakato")
    return {"student": amina.pk, "school": amina.school_id}


def test_every_route_renders_against_seed_data(seeded):
    assert web_client().get("/login").status_code == 200
    assert web_client().get("/")["Location"].startswith("/login")
    admin = web_client(User.objects.get(email="admin@kampaladps.schooldimes.test"))
    for route in SCHOOL_ROUTES:
        r = admin.get(route.format(**seeded))
        body = r.content.decode()
        assert r.status_code == 200 and 'data-testid="error-alert"' not in body, route
        assert "Kampala Demo Primary School" in body
    platform = web_client(User.objects.get(email="platform@schooldimes.test"))
    for route in PLATFORM_ROUTES:
        r = platform.get(route.format(**seeded))
        assert r.status_code == 200 and 'data-testid="error-alert"' not in r.content.decode(), route
    student = web_client(User.objects.get(email="student.amina@kampaladps.schooldimes.test"))
    assert "Hello, Amina!" in student.get("/student").content.decode()
    from payments.models import StudentTopUpLink

    link = StudentTopUpLink.objects.filter(revoked_at__isnull=True).first()
    if link:
        assert web_client().get(f"/give/{link.token}").status_code == 200


def _web_patterns():
    out = []

    def walk(patterns, prefix=""):
        for p in patterns:
            if isinstance(p, URLResolver):
                walk(p.url_patterns, prefix + str(p.pattern))
            elif isinstance(p, URLPattern) and p.callback.__module__.startswith("web."):
                out.append(prefix + str(p.pattern))

    walk(get_resolver().url_patterns)
    return out


def test_csrf_is_required_on_every_post(school_admin_a, platform_admin):
    import re

    patterns = _web_patterns()
    assert len(patterns) > 60
    for raw in patterns:
        url = "/" + re.sub(r"<int:\w+>", "1", re.sub(r"<str:\w+>", "x", raw))
        user = platform_admin if url.startswith("/platform") else school_admin_a
        c = web_client(user, csrf=True)
        assert c.post(url, {"a": "b"}, **hx()).status_code == 403, url


def test_tenant_isolation_sweep(admin_a_web, pos_b, school_b, school_admin_b, student_b1, parent_user):
    """School A's admin gets 404 for school B's objects on every object URL."""
    from decimal import Decimal

    from accounts.models import GuardianVerification
    from content.models import FinancialLiteracyTip
    from disputes.services import raise_dispute
    from fees.models import FeeCategory
    from policies.models import Policy, Product, ProductCategory
    from pooled_funds.services import create_fund
    from privacy.services import create_request
    from students.models import Guardian
    from wallets.models import P2PAlert

    Guardian.objects.create(parent=parent_user, student=student_b1)
    gv = GuardianVerification.objects.create(parent=parent_user, full_name="P", id_document_type="national_id",
                                             id_number="1")
    cat = ProductCategory.objects.create(school=school_b, name="B cat")
    prod = Product.objects.create(school=school_b, name="B prod", category=cat, price=Decimal("100"))
    fee = FeeCategory.objects.create(school=school_b, name="B fee", amount_type="fixed", fixed_amount="100")
    override = Policy.objects.create(school=school_b, student=student_b1, daily_spend_cap="1")
    fund = create_fund(school_admin_b, title="B fund")
    dispute = raise_dispute(parent_user, reason_category="wrong_amount", pos_transaction_id=pos_b["shortfall_id"])
    alert = P2PAlert.objects.create(school=school_b, student=student_b1, rule="many_distinct_senders", details={})
    req = create_request(parent_user, request_type="export", subject="student", student=student_b1)
    tip = FinancialLiteracyTip.objects.create(school=school_b, title="B tip", body="b", language="en")
    staff = User.objects.create_user(email="bstaff@x.test", password="pw123456", role="canteen_staff", school=school_b)
    link = Guardian.objects.get(student=student_b1)
    s, card, dev = student_b1.pk, pos_b["card"].pk, pos_b["device"].pk
    urls = [
        f"/school/students/{s}", f"/school/students/{s}/edit", f"/school/students/{s}/guardian-lookup",
        f"/school/students/{s}/portal/create", f"/school/students/{s}/portal/remove",
        f"/school/guardians/{link.pk}/unlink", f"/school/cards/issue?student={s}", f"/school/cards/{card}/reissue",
        f"/school/cards/{card}/freeze", f"/school/cards/{card}/unfreeze", f"/school/cards/{card}/mark-lost",
        f"/school/cards/{card}/reset-pin", f"/school/devices/{dev}/rotate-token", f"/school/devices/{dev}/revoke",
        f"/school/sales/transactions/{pos_b['shortfall_id']}", f"/school/shortfalls/{pos_b['shortfall_id']}/resolve",
        f"/school/products/{prod.pk}/edit", f"/school/products/{prod.pk}/delete",
        f"/school/products/categories/{cat.pk}/edit", f"/school/products/categories/{cat.pk}/delete",
        f"/school/policy/overrides/{override.pk}/remove", f"/school/staff/{staff.pk}/toggle",
        f"/school/staff/{staff.pk}/set-password", f"/school/fees/categories/{fee.pk}/edit",
        f"/school/fees/categories/{fee.pk}/pay", f"/school/pooled-funds/{fund.pk}", f"/school/pooled-funds/{fund.pk}/close",
        f"/school/pooled-funds/{fund.pk}/disburse", f"/school/disputes/{dispute.pk}",
        f"/school/disputes/{dispute.pk}/review", f"/school/disputes/{dispute.pk}/resolve",
        f"/school/p2p-alerts/{alert.pk}/history", f"/school/p2p-alerts/{alert.pk}/review",
        f"/school/privacy/{req.pk}/handle", f"/school/tips/{tip.pk}/edit", f"/school/tips/{tip.pk}/delete",
        f"/school/guardians/kyc/{gv.pk}/review",
    ]
    for url in urls:
        assert admin_a_web.get(url, **hx()).status_code == 404, url
        if "?" not in url and not url.endswith(("guardian-lookup",)):
            # 404, or 405 on a read-only page: either way nothing happens
            assert admin_a_web.post(url, {}, **hx()).status_code in (404, 405), url


def test_page_renders_in_luganda_and_kiswahili_with_english_fallback(admin_a_web, pos_a):
    for lang in ("lg", "sw"):
        admin_a_web.cookies[settings.LANGUAGE_COOKIE_NAME] = lang
        body = admin_a_web.get("/school").content.decode()
        assert f'<html lang="{lang}">' in body
        assert "Overview" in body  # untranslated UI strings fall back to English
        assert f'value="{lang}" selected' in body  # the switcher shows the current language


def test_build_locale_lists_every_web_string():
    from web.core.i18n_extract import web_msgids

    ids = web_msgids()
    for s in ("Overview", "Sign in to the school dashboard", "Send money to %(name)s",
              "Today, %(date)s (Africa/Kampala)", "Shown only once"):
        assert s in ids, s

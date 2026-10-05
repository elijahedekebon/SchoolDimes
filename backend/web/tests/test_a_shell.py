"""Section A: login/logout, role routing, refusal, throttle, language, bell."""
import pytest
from django.conf import settings

from notifications.models import NotificationEvent
from web.core.branding import brand_shades
from web.core.money import format_ugx, to_cents
from web.core.roles import decide_route

from .conftest import hx, web_client

pytestmark = pytest.mark.django_db


def login(client, email, password="pw123456", next_=None):
    url = "/login" + (f"?next={next_}" if next_ else "")
    return client.post(url, {"email": email, "password": password})


# -- pure helpers (were Vitest: roles.test.ts, money.test.ts) ------------------

def test_decide_route_rules():
    assert decide_route(None, "/school").to == "/login?next=/school"
    assert decide_route("school_admin", "/").to == "/school"
    assert decide_route("school_admin", "/platform").to == "/school"
    assert decide_route("platform_admin", "/school/sales").to == "/platform"
    assert decide_route("student", "/school").to == "/student"
    assert decide_route("platform_admin", "/platform/support").kind == "allow"
    for role in ("parent", "canteen_staff", "merchant_staff"):
        assert decide_route(role, "/school").kind == "refuse"
    assert decide_route(None, "/give/abc").kind == "allow"
    assert decide_route(None, "/login").kind == "allow"


def test_money_format_matches_dashboard():
    assert format_ugx("15000.00") == "UGX 15,000"
    assert format_ugx("15000.5") == "UGX 15,000.50"
    assert format_ugx("-500.00") == "-UGX 500"
    assert format_ugx(None) == "—" and format_ugx("abc") == "—"
    assert to_cents("1.234") is None and to_cents("0.1") == 10


def test_brand_shades_formula():
    shades = brand_shades("#0E7C66")
    assert len(shades) == 10 and shades[6] == "#0e7c66"
    assert shades[0] == "#ecf5f3"  # 14+241*.92 -> ec, like Providers.brandShades


# -- login ----------------------------------------------------------------------

def test_login_page_renders():
    r = web_client().get("/login")
    assert r.status_code == 200
    assert "Sign in to the school dashboard" in r.content.decode()


@pytest.mark.parametrize("fixture,home", [("school_admin_a", "/school"), ("platform_admin", "/platform"),
                                          ("student_login_a1", "/student")])
def test_login_routes_each_role_home(request, fixture, home):
    user = request.getfixturevalue(fixture)
    user.preferred_language = "sw"
    user.save()
    c = web_client()
    r = login(c, user.email)
    assert r.status_code == 302 and r["Location"] == home
    assert c.session.get("_auth_user_id") == str(user.pk)
    assert r.cookies[settings.LANGUAGE_COOKIE_NAME].value == "sw"


def test_login_next_only_within_home(school_admin_a):
    assert login(web_client(), school_admin_a.email, next_="/school/cards")["Location"] == "/school/cards"
    assert login(web_client(), school_admin_a.email, next_="/platform")["Location"] == "/school"
    assert login(web_client(), school_admin_a.email, next_="https://evil.example/school")["Location"] == "/school"


@pytest.mark.parametrize("fixture,text", [
    ("parent_user", "Parents use the SchoolDimes mobile app"),
    ("canteen_staff_a", "Canteen and merchant staff use the POS app"),
    ("merchant_staff", "Canteen and merchant staff use the POS app"),
])
def test_refused_roles_get_message_and_no_session(request, fixture, text):
    user = request.getfixturevalue(fixture)
    c = web_client()
    r = login(c, user.email)
    assert r.status_code == 403
    assert text in r.content.decode()
    assert "_auth_user_id" not in c.session


def test_wrong_password(school_admin_a):
    r = login(web_client(), school_admin_a.email, "nope")
    assert r.status_code == 401
    assert "No active account found" in r.content.decode()


def test_login_is_throttled(settings, school_admin_a):
    settings.AUTH_THROTTLE_RATE = "2/min"
    c = web_client()
    login(c, school_admin_a.email, "x")
    login(c, school_admin_a.email, "x")
    r = login(c, school_admin_a.email)
    assert r.status_code == 429
    assert "throttled" in r.content.decode().lower()


def test_session_cookie_is_httponly(school_admin_a):
    c = web_client()
    r = login(c, school_admin_a.email)
    assert r.cookies[settings.SESSION_COOKIE_NAME]["httponly"]


# -- routing --------------------------------------------------------------------

def test_root_redirects(school_admin_a, platform_admin):
    assert web_client().get("/")["Location"].startswith("/login")
    assert web_client(school_admin_a).get("/")["Location"] == "/school"
    assert web_client(platform_admin).get("/")["Location"] == "/platform"


def test_parent_with_a_session_is_refused_and_signed_out(parent_user):
    c = web_client(parent_user)
    r = c.get("/")
    assert r["Location"] == "/login?refused=1"
    assert "_auth_user_id" not in c.session


def test_expired_session_on_htmx_request():
    r = web_client().get("/notifications/bell", **hx())
    assert r["HX-Redirect"] == "/login?expired=1"


def test_logout_requires_csrf(school_admin_a):
    c = web_client(school_admin_a, csrf=True)
    assert c.post("/logout").status_code == 403
    c.get("/login")  # refused=0 -> keeps session; just to obtain a CSRF cookie
    token = c.cookies["csrftoken"].value
    r = c.post("/logout", {"csrfmiddlewaretoken": token})
    assert r.status_code == 302 and "_auth_user_id" not in c.session


# -- language -------------------------------------------------------------------

def test_language_switcher_updates_preferred_language(school_admin_a):
    c = web_client(school_admin_a)
    r = c.post("/locale", {"locale": "lg", "next": "/school"})
    assert r["Location"] == "/school"
    assert r.cookies[settings.LANGUAGE_COOKIE_NAME].value == "lg"
    school_admin_a.refresh_from_db()
    assert school_admin_a.preferred_language == "lg"


def test_language_switcher_signed_out_only_sets_cookie():
    r = web_client().post("/locale", {"locale": "sw", "next": "/give/x"})
    assert r.cookies[settings.LANGUAGE_COOKIE_NAME].value == "sw"
    assert web_client().post("/locale", {"locale": "xx"}).cookies.get(settings.LANGUAGE_COOKIE_NAME) is None


# -- notifications bell -----------------------------------------------------------

def _note(user, title, read=False):
    from django.utils import timezone

    return NotificationEvent.objects.create(user=user, event_type="test", title=title, body="b",
                                            read_at=timezone.now() if read else None)


def test_bell_lists_own_notifications_and_marks_read(school_admin_a, school_admin_b):
    mine = _note(school_admin_a, "Mine")
    _note(school_admin_a, "Old", read=True)
    theirs = _note(school_admin_b, "Theirs")
    c = web_client(school_admin_a)
    body = c.get("/notifications/bell", **hx()).content.decode()
    assert "Mine" in body and "Old" in body and "Theirs" not in body
    assert '<span class="indicator">1</span>' in body
    assert c.post(f"/notifications/{theirs.pk}/read", **hx()).status_code == 404
    c.post(f"/notifications/{mine.pk}/read", **hx())
    mine.refresh_from_db()
    assert mine.read_at is not None
    _note(school_admin_a, "New")
    c.post("/notifications/read-all", **hx())
    assert not NotificationEvent.objects.filter(user=school_admin_a, read_at__isnull=True).exists()
    theirs.refresh_from_db()
    assert theirs.read_at is None

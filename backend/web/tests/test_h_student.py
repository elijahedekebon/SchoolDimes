"""Section H: student portal (school-issued login), read-only, only their own data."""
import pytest

from .conftest import web_client

pytestmark = pytest.mark.django_db


def test_student_sees_only_own_summary(pos_a, school_admin_a, student_a2):
    from conftest import fund_wallet
    from students.portal import create_portal_account
    from wallets.services import ensure_student_wallets

    student = pos_a["student"]
    login = create_portal_account(school_admin_a, student, email="me@portal.test", password="pw123456").user
    other_main, _ = ensure_student_wallets(student_a2)
    fund_wallet(other_main, "77700")
    c = web_client()
    assert c.post("/login", {"email": "me@portal.test", "password": "pw123456"})["Location"] == "/student"
    body = c.get("/student").content.decode()
    first = student.name.split()[0]
    assert f"Hello, {first}!" in body and "Rice" in body and 'data-testid="portal-balance"' in body
    assert student_a2.name not in body and "77,700" not in body
    assert "data-testid=\"bell\"" not in body  # the student frame has no notifications bell
    for url in ("/school", "/school/students", "/platform"):
        assert c.get(url)["Location"] == "/student"
    assert login.role == "student"


def test_other_roles_cannot_open_the_portal(school_admin_a, platform_admin, parent_user, canteen_staff_a):
    assert web_client(school_admin_a).get("/student")["Location"] == "/school"
    assert web_client(platform_admin).get("/student")["Location"] == "/platform"
    for user in (parent_user, canteen_staff_a):
        assert web_client(user).get("/student")["Location"] == "/login?refused=1"


def test_student_login_is_rate_limited(settings, student_login_a1):
    settings.AUTH_THROTTLE_RATE = "1/min"
    c = web_client()
    c.post("/login", {"email": student_login_a1.email, "password": "wrong"})
    assert c.post("/login", {"email": student_login_a1.email, "password": "pw123456"}).status_code == 429

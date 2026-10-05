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

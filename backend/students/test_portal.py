"""Part 4A Section H: student portal accounts and the student allowlist."""
import pytest
from rest_framework.test import APIClient

from accounts.models import User
from conftest import client_for, fund_wallet
from content.models import FinancialLiteracyTip
from wallets.services import ensure_student_wallets


def login(email, password="longpassword1"):
    c = APIClient()
    tokens = c.post("/api/v1/auth/login", {"email": email, "password": password}, format="json").data
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
    return c


@pytest.fixture
def portal(db, school_admin_a, student_a1):
    main, _ = ensure_student_wallets(student_a1)
    fund_wallet(main, "4500")
    r = client_for(school_admin_a).post(f"/api/v1/students/{student_a1.pk}/portal-account/",
                                        {"email": "amina@student.test", "password": "longpassword1"}, format="json")
    assert r.status_code == 201, r.data
    return login("amina@student.test")


@pytest.mark.django_db
class TestPortalAccount:
    def test_admin_creates_reads_removes(self, school_admin_a, student_a1, portal):
        c = client_for(school_admin_a)
        assert c.get(f"/api/v1/students/{student_a1.pk}/portal-account/").data["email"] == "amina@student.test"
        assert c.post(f"/api/v1/students/{student_a1.pk}/portal-account/",
                      {"email": "x@student.test", "password": "longpassword1"}, format="json").status_code == 409
        assert c.delete(f"/api/v1/students/{student_a1.pk}/portal-account/").status_code == 204
        assert not User.objects.filter(email="amina@student.test").exists()
        assert c.get(f"/api/v1/students/{student_a1.pk}/portal-account/").status_code == 404

    def test_other_school_admin_and_parent_refused(self, school_admin_b, parent_user, guardian_link_a1, student_a1):
        body = {"email": "y@student.test", "password": "longpassword1"}
        assert client_for(school_admin_b).post(f"/api/v1/students/{student_a1.pk}/portal-account/", body,
                                               format="json").status_code == 404
        assert client_for(parent_user).post(f"/api/v1/students/{student_a1.pk}/portal-account/", body,
                                            format="json").status_code == 403


@pytest.mark.django_db
class TestPortalSummary:
    def test_student_sees_only_own_summary(self, portal, student_a1):
        FinancialLiteracyTip.objects.create(title="Save a little", body="…", language="en")
        r = portal.get("/api/v1/student-portal/me/")
        assert r.status_code == 200, r.data
        assert r.data["student"]["id"] == student_a1.pk
        assert r.data["main_balance"] == "4500.00"
        assert r.data["tip"]["title"] == "Save a little"
        assert "pin_hash" not in str(r.data)

    def test_student_login_cannot_reach_school_data(self, portal, student_a2, card_a1):
        for path in ("/api/v1/students/", f"/api/v1/students/{student_a2.pk}/", "/api/v1/wallets/", "/api/v1/cards/",
                     "/api/v1/guardians/", "/api/v1/pos/transactions/", "/api/v1/analytics/sales-summary/",
                     "/api/v1/policies/", "/api/v1/notifications/"):
            assert portal.get(path).status_code == 403, path
        assert portal.get("/api/v1/me").status_code == 200
        assert portal.get("/api/v1/my-school/").status_code == 200

    def test_non_students_refused(self, school_admin_a, parent_user):
        assert client_for(school_admin_a).get("/api/v1/student-portal/me/").status_code == 403
        assert client_for(parent_user).get("/api/v1/student-portal/me/").status_code == 403

"""Part 4A: GET /my-school/ and CORS for the dashboard origin."""
import pytest

from conftest import client_for
from students.models import Guardian


@pytest.mark.django_db
class TestMySchool:
    def test_staff_sees_own_school_branding(self, school_a, school_admin_a):
        school_a.branding = {"logo_url": "https://x/logo.png", "primary_color": "#123456"}
        school_a.save()
        r = client_for(school_admin_a).get("/api/v1/my-school/")
        assert r.status_code == 200
        assert r.data["school"]["name"] == school_a.name
        assert r.data["school"]["branding"]["primary_color"] == "#123456"
        assert "policy_defaults" not in r.data["school"]

    def test_parent_sees_only_linked_students_schools(self, parent_user, student_a1, school_b):
        Guardian.objects.create(parent=parent_user, student=student_a1)
        r = client_for(parent_user).get("/api/v1/my-school/")
        assert r.data["school"] is None
        assert [s["id"] for s in r.data["schools"]] == [student_a1.school_id]

    def test_platform_admin_has_no_school(self, platform_admin):
        r = client_for(platform_admin).get("/api/v1/my-school/")
        assert r.data == {"school": None, "schools": []}

    def test_anonymous_refused(self, api_client):
        assert api_client.get("/api/v1/my-school/").status_code == 401


@pytest.mark.django_db
def test_cors_allows_configured_origin_only(api_client, settings):
    settings.CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]
    ok = api_client.options("/api/v1/auth/login", HTTP_ORIGIN="http://localhost:3000",
                            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST")
    assert ok["access-control-allow-origin"] == "http://localhost:3000"
    bad = api_client.options("/api/v1/auth/login", HTTP_ORIGIN="http://evil.example",
                             HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST")
    assert "access-control-allow-origin" not in bad


@pytest.mark.django_db
def test_login_is_throttled(api_client, school_admin_a, settings):
    settings.AUTH_THROTTLE_RATE = "3/min"
    codes = [
        api_client.post("/api/v1/auth/login", {"email": school_admin_a.email, "password": "wrong"},
                        format="json").status_code
        for _ in range(4)
    ]
    assert codes[:3] == [401, 401, 401]
    assert codes[3] == 429

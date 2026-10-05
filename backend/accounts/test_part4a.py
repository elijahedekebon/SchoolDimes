"""Part 4A: KYC review and parent lookup."""
import pytest

from accounts.models import GuardianVerification
from conftest import client_for


@pytest.fixture
def verification(db, parent_user):
    return GuardianVerification.objects.create(parent=parent_user, full_name="P", id_number="CM123")


@pytest.mark.django_db
class TestKycReview:
    def test_school_admin_of_linked_school_approves(self, school_admin_a, guardian_link_a1, verification):
        r = client_for(school_admin_a).post(f"/api/v1/guardian-verifications/{verification.pk}/review/",
                                            {"status": "verified", "review_notes": "ID checked"}, format="json")
        assert r.status_code == 200, r.data
        assert r.data["status"] == "verified" and r.data["verified_at"]
        assert r.data["review_notes"] == "ID checked" and r.data["reviewed_by"] == school_admin_a.pk

    def test_reject_clears_verified_at(self, school_admin_a, guardian_link_a1, verification):
        c = client_for(school_admin_a)
        c.post(f"/api/v1/guardian-verifications/{verification.pk}/review/", {"status": "verified"}, format="json")
        r = c.post(f"/api/v1/guardian-verifications/{verification.pk}/review/", {"status": "rejected"}, format="json")
        assert r.data["status"] == "rejected" and r.data["verified_at"] is None

    def test_other_school_admin_gets_404(self, school_admin_b, guardian_link_a1, verification):
        r = client_for(school_admin_b).post(f"/api/v1/guardian-verifications/{verification.pk}/review/",
                                            {"status": "verified"}, format="json")
        assert r.status_code == 404

    def test_parent_cannot_review_self(self, parent_user, verification):
        r = client_for(parent_user).post(f"/api/v1/guardian-verifications/{verification.pk}/review/",
                                         {"status": "verified"}, format="json")
        assert r.status_code == 403


@pytest.mark.django_db
class TestUserLookup:
    def test_exact_email_parent_only(self, school_admin_a, parent_user, school_admin_b):
        c = client_for(school_admin_a)
        r = c.get("/api/v1/users/lookup/", {"email": parent_user.email.upper()})
        assert r.status_code == 200 and r.data["id"] == parent_user.pk
        assert c.get("/api/v1/users/lookup/", {"email": "parent@"}).status_code == 404
        assert c.get("/api/v1/users/lookup/", {"email": school_admin_b.email}).status_code == 404

    def test_parent_cannot_lookup(self, parent_user):
        assert client_for(parent_user).get("/api/v1/users/lookup/", {"email": "x@y.z"}).status_code == 403

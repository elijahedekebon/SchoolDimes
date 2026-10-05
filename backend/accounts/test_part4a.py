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


@pytest.mark.django_db
class TestStaffUsers:
    def _merchant(self, school, admin):
        from merchants.models import Merchant, MerchantApproval

        m = Merchant.objects.create(name="Shop", created_by=admin)
        MerchantApproval.objects.create(merchant=m, school=school, status="approved")
        return m

    def test_school_admin_creates_canteen_staff_in_own_school(self, school_admin_a, school_b):
        r = client_for(school_admin_a).post("/api/v1/users/", {
            "email": "till@a.test", "password": "longpassword", "role": "canteen_staff",
            "full_name": "Till", "school": school_b.pk}, format="json")
        assert r.status_code == 201, r.data
        assert r.data["school"] == school_admin_a.school_id  # client-supplied school ignored
        assert "password" not in r.data

    def test_merchant_staff_linked_in_one_step(self, school_admin_a, school_a):
        m = self._merchant(school_a, school_admin_a)
        c = client_for(school_admin_a)
        r = c.post("/api/v1/users/", {"email": "shop@a.test", "password": "longpassword",
                                      "role": "merchant_staff", "merchant": m.pk}, format="json")
        assert r.status_code == 201, r.data
        assert r.data["merchant_id"] == m.pk and r.data["school"] is None
        assert any(u["email"] == "shop@a.test" for u in c.get("/api/v1/users/").data["results"])

    def test_cannot_link_merchant_not_approved_for_school(self, school_admin_a, school_admin_b, school_b):
        m = self._merchant(school_b, school_admin_b)
        r = client_for(school_admin_a).post("/api/v1/users/", {"email": "x@a.test", "password": "longpassword",
                                                               "role": "merchant_staff", "merchant": m.pk}, format="json")
        assert r.status_code == 403
        from accounts.models import User
        assert not User.objects.filter(email="x@a.test").exists()  # rolled back

    def test_cannot_create_parent_or_platform_admin(self, school_admin_a):
        for role in ("parent", "platform_admin"):
            r = client_for(school_admin_a).post("/api/v1/users/", {"email": f"{role}@a.test", "password": "longpassword",
                                                                   "role": role}, format="json")
            assert r.status_code == 400

    def test_isolation_and_parent_refused(self, school_admin_a, school_admin_b, parent_user):
        c = client_for(school_admin_a)
        emails = [u["email"] for u in c.get("/api/v1/users/").data["results"]]
        assert school_admin_b.email not in emails and parent_user.email not in emails
        assert c.get(f"/api/v1/users/{school_admin_b.pk}/").status_code == 404
        assert client_for(parent_user).get("/api/v1/users/").status_code == 403

    def test_deactivate_and_set_password(self, school_admin_a):
        c = client_for(school_admin_a)
        u = c.post("/api/v1/users/", {"email": "t2@a.test", "password": "longpassword", "role": "canteen_staff"},
                   format="json").data
        assert c.patch(f"/api/v1/users/{u['id']}/", {"is_active": False}, format="json").data["is_active"] is False
        assert c.post(f"/api/v1/users/{u['id']}/set-password/", {"password": "newpassword1"}, format="json").status_code == 200
        assert c.patch(f"/api/v1/users/{school_admin_a.pk}/", {"is_active": False}, format="json").status_code == 409

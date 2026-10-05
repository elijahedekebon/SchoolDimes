"""Part 4A: student list filters and detail access."""
import pytest

from conftest import client_for
from students.models import Student


@pytest.mark.django_db
class TestStudentFilters:
    def test_search_by_name_or_class_scoped_to_school(self, school_admin_a, student_a1, student_a2, student_b1):
        Student.objects.create(school=student_b1.school, name="Amina Other School", class_name="P4")
        c = client_for(school_admin_a)
        names = [s["name"] for s in c.get("/api/v1/students/?search=amina").data["results"]]
        assert names == [student_a1.name]
        assert c.get("/api/v1/students/?search=p4").data["count"] == 2
        assert c.get("/api/v1/students/?class_name=P5").data["count"] == 0


@pytest.mark.django_db
class TestStudentDetailAndFilters:
    def test_parent_can_read_own_child_detail_not_others(self, parent_user, guardian_link_a1, student_a1, student_a2):
        c = client_for(parent_user)
        assert c.get(f"/api/v1/students/{student_a1.pk}/").status_code == 200
        assert c.get(f"/api/v1/students/{student_a2.pk}/").status_code == 404

    def test_other_school_admin_gets_404(self, school_admin_b, student_a1):
        assert client_for(school_admin_b).get(f"/api/v1/students/{student_a1.pk}/").status_code == 404

    def test_card_status_and_low_balance(self, school_admin_a, student_a1, student_a2):
        from cards.services import issue_card
        from conftest import fund_wallet
        from wallets.services import ensure_student_wallets

        issue_card(student_a1, "1234")
        frozen = issue_card(student_a2, "1234")
        frozen.status = "frozen"
        frozen.save()
        main1, _ = ensure_student_wallets(student_a1)
        ensure_student_wallets(student_a2)
        fund_wallet(main1, "10000")
        c = client_for(school_admin_a)
        ids = lambda q: [s["id"] for s in c.get(f"/api/v1/students/?{q}").data["results"]]  # noqa: E731
        assert ids("card_status=frozen") == [student_a2.pk]
        assert ids("card_status=active") == [student_a1.pk]
        assert ids("low_balance=true") == [student_a2.pk]


@pytest.mark.django_db
def test_guardian_display_fields_and_parent_only(school_admin_a, guardian_link_a1, student_a2, school_admin_b):
    c = client_for(school_admin_a)
    row = c.get("/api/v1/guardians/", {"student": guardian_link_a1.student_id}).data["results"][0]
    assert row["parent_email"] == guardian_link_a1.parent.email and row["verification_status"] is None
    r = c.post("/api/v1/guardians/", {"parent": school_admin_b.pk, "student": student_a2.pk, "relationship": "other"}, format="json")
    assert r.status_code == 400


@pytest.mark.django_db
def test_admin_cannot_link_guardian_to_other_school_student(school_admin_b, parent_user, student_a1):
    r = client_for(school_admin_b).post("/api/v1/guardians/", {"parent": parent_user.pk, "student": student_a1.pk,
                                                                "relationship": "mother"}, format="json")
    assert r.status_code == 404

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

"""Part 4A: policy list filters."""
import pytest

from conftest import client_for
from policies.models import Policy


@pytest.mark.django_db
def test_policy_filters(school_admin_a, student_a1, student_a2, school_admin_b):
    Policy.objects.create(school=student_a1.school, student=student_a1, daily_spend_cap="1000")
    c = client_for(school_admin_a)
    c.get("/api/v1/policies/")  # creates the school default
    assert c.get("/api/v1/policies/", {"kind": "default"}).data["count"] == 1
    assert c.get("/api/v1/policies/", {"kind": "override"}).data["count"] == 1
    assert c.get("/api/v1/policies/", {"student": student_a1.pk}).data["count"] == 1
    assert c.get("/api/v1/policies/", {"student": student_a2.pk}).data["count"] == 0
    assert client_for(school_admin_b).get("/api/v1/policies/", {"student": student_a1.pk}).data["count"] == 0

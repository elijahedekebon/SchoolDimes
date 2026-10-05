"""Part 4A: ?status= / ?request_type= filters on the data-request queue."""
import pytest

from conftest import client_for
from privacy.models import DataRequest


@pytest.mark.django_db
def test_data_request_status_filter(school_admin_a, parent_user, student_a1, guardian_link_a1, school_admin_b):
    DataRequest.objects.create(requested_by=parent_user, request_type="export", subject="self",
                               school=student_a1.school, status="pending")
    DataRequest.objects.create(requested_by=parent_user, request_type="deletion", subject="self",
                               school=student_a1.school, status="completed")
    c = client_for(school_admin_a)
    assert c.get("/api/v1/privacy/data-requests/?status=pending").data["count"] == 1
    assert c.get("/api/v1/privacy/data-requests/?request_type=deletion").data["count"] == 1
    assert client_for(school_admin_b).get("/api/v1/privacy/data-requests/?status=pending").data["count"] == 0

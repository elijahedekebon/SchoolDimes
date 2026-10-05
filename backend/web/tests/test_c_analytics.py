"""Section C: analytics charts + tables, per-student spending, isolation."""
import pytest

from .conftest import hx

pytestmark = pytest.mark.django_db


def test_analytics_page_renders_charts_and_tables(admin_a_web, pos_a):
    body = admin_a_web.get("/school/analytics").content.decode()
    for chart in ("best-chart", "peak-chart", "cat-chart"):
        assert f'id="{chart}"' in body
    assert "Rice" in body and "Meals" in body
    assert "Sales sent without line items aren't in this breakdown." in body  # simplified, labelled
    assert "Choose a student to see their spending in this period." in body


def test_per_student_spending(admin_a_web, pos_a):
    r = admin_a_web.get("/school/analytics", {"student": pos_a["student"].pk}, **hx("student_spending"))
    body = r.content.decode()
    assert body.startswith('<div id="student_spending">') and "UGX 10,000" in body  # purchases total


def test_per_student_spending_other_school_is_not_found(admin_a_web, pos_b):
    body = admin_a_web.get("/school/analytics", {"student": pos_b["student"].pk}, **hx("student_spending")).content.decode()
    assert 'data-testid="error-alert"' in body and "not_found" in body


def test_student_picker_is_tenant_scoped(admin_a_web, student_a1, student_b1):
    body = admin_a_web.get("/school/_picker/students", {"q": ""}, **hx()).content.decode()
    assert student_a1.name in body and student_b1.name not in body
    body = admin_a_web.get("/school/_picker/students", {"q": "Brian"}, **hx()).content.decode()
    assert student_a1.name not in body


def test_bad_range_shows_backend_message(admin_a_web):
    body = admin_a_web.get("/school/analytics", {"from": "2026-05-01", "to": "2026-01-01"},
                           **hx("analytics_body")).content.decode()
    assert "range_invalid" in body

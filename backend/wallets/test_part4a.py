"""Part 4A: ?student= filters on wallets and savings goals."""
import pytest

from conftest import client_for
from wallets.models import SavingsGoal
from wallets.services import ensure_student_wallets


@pytest.mark.django_db
def test_wallet_and_goal_student_filters(school_admin_a, student_a1, student_a2, school_admin_b):
    m1, s1 = ensure_student_wallets(student_a1)
    ensure_student_wallets(student_a2)
    SavingsGoal.objects.create(wallet=s1, goal_name="Bike", target_amount="50000")
    c = client_for(school_admin_a)
    rows = c.get("/api/v1/wallets/", {"student": student_a1.pk}).data["results"]
    assert {w["wallet_type"] for w in rows} == {"main", "savings"}
    assert c.get("/api/v1/wallets/", {"student": student_a1.pk, "wallet_type": "main"}).data["count"] == 1
    assert c.get("/api/v1/savings-goals/", {"student": student_a1.pk}).data["count"] == 1
    assert c.get("/api/v1/savings-goals/", {"student": student_a2.pk}).data["count"] == 0
    assert client_for(school_admin_b).get("/api/v1/wallets/", {"student": student_a1.pk}).data["count"] == 0

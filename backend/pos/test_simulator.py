"""simulate_pos, mock_webhook and run_recurring_topups run end-to-end (CI mode)."""
import io

import pytest
from django.core.management import call_command

from conftest import assert_books_balanced
from payments.models import Deposit
from pos.management.commands.simulate_pos import DjangoTransport, run_simulation
from tenants.models import School


@pytest.mark.django_db
def test_simulate_pos_end_to_end():
    call_command("seed_demo", stdout=io.StringIO())
    lines = []
    summary = run_simulation(DjangoTransport(), log=lines.append)
    assert set(summary["replay_statuses"]) == {"duplicate"}
    assert len(summary["shortfalls"]) == 1
    flags = {f for r in summary["flagged"] for f in r["flags"]}
    assert {"card_frozen", "item_blocked", "exceeds_offline_ceiling"} <= flags
    assert summary["rejected"] == []
    assert summary["attendance_created"] == 3
    assert [a["status"] for a in summary["attendance"]].count("duplicate") == 1
    assert any("POS SIMULATION SUMMARY" in line for line in lines)
    assert_books_balanced(*School.objects.all())
    # runs again cleanly (new idempotency keys, rotated tokens)
    again = run_simulation(DjangoTransport(), log=lambda *_: None)
    assert set(again["replay_statuses"]) == {"duplicate"}
    assert_books_balanced(*School.objects.all())


@pytest.mark.django_db
def test_mock_webhook_and_recurring_commands():
    call_command("seed_demo", stdout=io.StringIO())
    pending = Deposit.objects.get(status="pending")
    out = io.StringIO()
    call_command("mock_webhook", pending.reference, stdout=out)
    assert "confirmed" in out.getvalue()
    pending.refresh_from_db()
    assert pending.status == "confirmed"
    out = io.StringIO()
    call_command("mock_webhook", pending.reference, stdout=out)
    assert "duplicate" in out.getvalue()

    out = io.StringIO()
    call_command("run_recurring_topups", "--now", stdout=out)
    assert "confirmed" in out.getvalue()
    assert_books_balanced(*School.objects.all())

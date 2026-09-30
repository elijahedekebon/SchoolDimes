from datetime import datetime
from zoneinfo import ZoneInfo

import pytest

from attendance.models import AttendanceRecord
from cards.services import issue_card
from conftest import client_for
from notifications.models import NotificationEvent
from pos.services import register_device
from pos.tests import device_client
from tenants.services import get_school_settings

KAMPALA = ZoneInfo("Africa/Kampala")


@pytest.fixture
def gate(school_admin_a, school_a):
    device, raw = register_device(school_admin_a, school=school_a, device_name="Main gate", device_role="attendance")
    return device, device_client(raw)


def tap(card, key, hour=7, minute=30, direction="in", day=30):
    return {"idempotency_key": key, "card_uid": card.card_uid, "direction": direction,
            "device_local_timestamp": datetime(2026, 9, day, hour, minute, tzinfo=KAMPALA).isoformat()}


@pytest.mark.django_db
class TestAttendance:
    def test_single_and_batch_with_duplicates(self, gate, card_a1, student_a1):
        single = gate[1].post("/api/v1/attendance/tap/", tap(card_a1, "t1"), format="json")
        assert single.status_code == 200 and single.data["results"][0]["status"] == "created"
        batch = gate[1].post("/api/v1/attendance/tap/", {"taps": [
            tap(card_a1, "t1"),                                   # duplicate of the single tap
            tap(card_a1, "t2", hour=16, direction="out"),
            tap(card_a1, "t2", hour=16, direction="out"),         # duplicate inside the batch
            {**tap(card_a1, "t3"), "card_uid": "nope"},
            {**tap(card_a1, "t4"), "direction": "sideways"},
        ]}, format="json").data
        assert [r["status"] for r in batch["results"]] == ["duplicate", "created", "duplicate", "rejected", "rejected"]
        assert batch["created"] == 1
        assert AttendanceRecord.objects.filter(student=student_a1).count() == 2

    def test_no_money_moves_and_canteen_needs_setting(self, school_admin_a, school_a, card_a1):
        from wallets.models import LedgerEntry

        device, raw = register_device(school_admin_a, school=school_a, device_name="Till", device_role="canteen")
        client = device_client(raw)
        assert client.post("/api/v1/attendance/tap/", tap(card_a1, "c1"), format="json").status_code == 403
        settings_row = get_school_settings(school_a)
        settings_row.attendance_on_canteen_devices = True
        settings_row.save()
        assert client.post("/api/v1/attendance/tap/", tap(card_a1, "c1"), format="json").data["created"] == 1
        assert LedgerEntry.objects.count() == 0

    def test_attendance_device_cannot_sell(self, gate):
        assert gate[1].get("/api/v1/pos/cache/").status_code == 403

    def test_tenant_scoping(self, school_admin_b, school_b, card_a1, gate, admin_b_client, student_b1):
        _, raw = register_device(school_admin_b, school=school_b, device_name="B gate", device_role="attendance")
        result = device_client(raw).post("/api/v1/attendance/tap/", tap(card_a1, "x"), format="json").data
        assert result["results"][0]["reason"] == "unknown_card"  # school A card at school B gate
        gate[1].post("/api/v1/attendance/tap/", tap(card_a1, "a"), format="json")
        assert admin_b_client.get("/api/v1/attendance/").data["count"] == 0
        student_b_id = card_a1.student_id
        assert admin_b_client.get(f"/api/v1/students/{student_b_id}/attendance/").status_code == 404

    def test_listing_by_date_and_guardian_view(self, gate, card_a1, student_a1, admin_a_client, parent_client,
                                               guardian_link_a1, other_parent):
        gate[1].post("/api/v1/attendance/tap/", {"taps": [
            tap(card_a1, "d1", day=29), tap(card_a1, "d2", day=30), tap(card_a1, "d3", hour=16, day=30, direction="out"),
        ]}, format="json")
        assert admin_a_client.get("/api/v1/attendance/?date=2026-09-30").data["count"] == 2
        assert admin_a_client.get("/api/v1/attendance/?date=2026-09-30&direction=in").data["count"] == 1
        assert parent_client.get(f"/api/v1/students/{student_a1.pk}/attendance/?from=2026-09-29&to=2026-09-30").data["count"] == 3
        assert parent_client.get("/api/v1/attendance/").data["count"] == 3
        assert client_for(other_parent).get("/api/v1/attendance/").data["count"] == 0
        assert client_for(other_parent).get(f"/api/v1/students/{student_a1.pk}/attendance/").status_code == 404

    def test_first_tap_in_notification_is_opt_in(self, gate, card_a1, guardian_link_a1, parent_user, school_a):
        gate[1].post("/api/v1/attendance/tap/", tap(card_a1, "n1", day=28), format="json")
        assert not NotificationEvent.objects.filter(event_type="attendance_tap_in").exists()
        s = get_school_settings(school_a)
        s.attendance_notify_guardians = True
        s.save()
        gate[1].post("/api/v1/attendance/tap/", {"taps": [tap(card_a1, "n2"), tap(card_a1, "n3", hour=9)]}, format="json")
        events = NotificationEvent.objects.filter(user=parent_user, event_type="attendance_tap_in")
        assert events.count() == 1 and "07:30" in events.get().body

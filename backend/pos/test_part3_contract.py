"""Part 3 contract additions: /pos/device/, /attendance/roster/, week_spend."""
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from conftest import fund_wallet
from pos.services import register_device, sync_batch
from tenants.services import get_school_settings
from wallets.services import ensure_student_wallets


def device_client(token):
    c = APIClient()
    c.credentials(HTTP_AUTHORIZATION=f"Device {token}")
    return c


@pytest.fixture
def setup(db, school_admin_a, school_a, student_a1, school_admin_b, school_b, student_b1):
    from cards.services import issue_card

    main, _ = ensure_student_wallets(student_a1)
    fund_wallet(main, "10000")
    card = issue_card(student_a1, "1234", card_uid="04aa11bb")
    issue_card(student_b1, "1234", card_uid="04bb22cc")
    canteen, ctoken = register_device(school_admin_a, school=school_a, device_name="Till", device_role="canteen")
    gate, gtoken = register_device(school_admin_a, school=school_a, device_name="Gate", device_role="attendance")
    return {"card": card, "canteen": canteen, "ctoken": ctoken, "gate": gate, "gtoken": gtoken}


@pytest.mark.django_db
class TestDeviceInfo:
    def test_every_role_can_identify_itself(self, setup, school_a):
        for token, role in ((setup["ctoken"], "canteen"), (setup["gtoken"], "attendance")):
            r = device_client(token).get("/api/v1/pos/device/")
            assert r.status_code == 200, r.data
            assert r.data["device_role"] == role and r.data["school"]["name"] == school_a.name
            assert r.data["school"]["default_language"] in ("en", "lg", "sw")
            assert r.data["can_sell"] is (role == "canteen")
            assert r.data["can_record_attendance"] is (role == "attendance")

    def test_revoked_and_jwt_refused(self, setup, school_admin_a):
        from pos.services import revoke_device

        revoke_device(school_admin_a, setup["gate"])
        assert device_client(setup["gtoken"]).get("/api/v1/pos/device/").status_code == 401
        c = APIClient()
        c.force_authenticate(school_admin_a)
        assert c.get("/api/v1/pos/device/").status_code in (401, 403)


@pytest.mark.django_db
class TestRoster:
    def test_gate_gets_own_school_names_without_secrets(self, setup):
        r = device_client(setup["gtoken"]).get("/api/v1/attendance/roster/")
        assert r.status_code == 200
        assert [c["card_uid"] for c in r.data["cards"]] == ["04aa11bb"]  # not school B's card
        row = r.data["cards"][0]
        assert row["student_display_name"] and "pin_hash" not in row and "balance" not in row

    def test_incremental(self, setup):
        first = device_client(setup["gtoken"]).get("/api/v1/attendance/roster/").data
        again = device_client(setup["gtoken"]).get("/api/v1/attendance/roster/", {"since": first["generated_at"]}).data
        assert again["cards"] == []
        setup["card"].status = "frozen"
        setup["card"].save()
        again = device_client(setup["gtoken"]).get("/api/v1/attendance/roster/", {"since": first["generated_at"]}).data
        assert [c["status"] for c in again["cards"]] == ["frozen"]

    def test_canteen_only_when_school_allows(self, setup, school_a):
        assert device_client(setup["ctoken"]).get("/api/v1/attendance/roster/").status_code == 403
        s = get_school_settings(school_a)
        s.attendance_on_canteen_devices = True
        s.save()
        assert device_client(setup["ctoken"]).get("/api/v1/attendance/roster/").status_code == 200


@pytest.mark.django_db
def test_cache_has_week_spend(setup):
    sync_batch(setup["canteen"], [{"idempotency_key": "w1", "card_uid": "04aa11bb", "amount": "1500.00",
                                   "device_local_timestamp": "2026-10-05T10:00:00+03:00"}])
    from freezegun import freeze_time

    with freeze_time("2026-10-07T09:00:00+03:00"):  # Wednesday of the same week
        r = device_client(setup["ctoken"]).get("/api/v1/pos/cache/")
    row = r.data["cards"][0]
    assert r.data["week_start"] == "2026-10-05"
    assert row["week_spend"] == "1500.00" and row["today_spend"] == "0.00"
    assert Decimal(row["balance"]) == Decimal("8500.00")

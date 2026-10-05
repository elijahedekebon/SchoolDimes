"""Part 4A: issue/reissue with a real NFC UID, UID normalisation, PIN reset."""
import pytest
from django.contrib.auth.hashers import check_password

from cards.models import Card
from cards.services import normalize_card_uid
from conftest import client_for


@pytest.mark.parametrize(
    "raw,expected",
    [
        ("04:A2:2B:7C:91:3E:80", "04a22b7c913e80"),
        ("04 a2 2b 7c", "04a22b7c"),
        ("04-A2-2B-7C-91-3E-80", "04a22b7c913e80"),
        ("45eb3e68775a49aea1f0ec9c0406bea8", "45eb3e68775a49aea1f0ec9c0406bea8"),
    ],
)
def test_normalize_card_uid(raw, expected):
    assert normalize_card_uid(raw) == expected


@pytest.mark.parametrize("raw", ["", "04a2", "04a22b7", "zz112233", "04:a2:2b:7c:9"])
def test_normalize_card_uid_rejects_bad_input(raw):
    with pytest.raises(ValueError):
        normalize_card_uid(raw)


@pytest.mark.django_db
class TestIssueWithUid:
    def test_issue_with_nfc_uid_is_normalised(self, school_admin_a, student_a1):
        r = client_for(school_admin_a).post(
            "/api/v1/cards/issue/", {"student": student_a1.pk, "pin": "1234", "card_uid": "04:A2:2B:7C:91:3E:80"},
            format="json")
        assert r.status_code == 201, r.data
        assert r.data["card_uid"] == "04a22b7c913e80"
        assert "pin_hash" not in r.data

    def test_duplicate_uid_rejected(self, school_admin_a, student_a1, student_a2):
        c = client_for(school_admin_a)
        c.post("/api/v1/cards/issue/", {"student": student_a1.pk, "pin": "1234", "card_uid": "04a22b7c"}, format="json")
        r = c.post("/api/v1/cards/issue/", {"student": student_a2.pk, "pin": "1234", "card_uid": "04:A2:2B:7C"}, format="json")
        assert r.status_code == 400 and "card_uid" in r.data

    def test_bad_uid_rejected(self, school_admin_a, student_a1):
        r = client_for(school_admin_a).post(
            "/api/v1/cards/issue/", {"student": student_a1.pk, "pin": "1234", "card_uid": "hello"}, format="json")
        assert r.status_code == 400 and "card_uid" in r.data

    def test_without_uid_server_generates_one(self, school_admin_a, student_a1):
        r = client_for(school_admin_a).post("/api/v1/cards/issue/", {"student": student_a1.pk, "pin": "1234"}, format="json")
        assert r.status_code == 201 and len(r.data["card_uid"]) == 32

    def test_reissue_with_uid(self, school_admin_a, card_a1):
        r = client_for(school_admin_a).post(f"/api/v1/cards/{card_a1.pk}/reissue/",
                                            {"pin": "5678", "card_uid": "AA:BB:CC:DD"}, format="json")
        assert r.status_code == 201 and r.data["card_uid"] == "aabbccdd"
        card_a1.refresh_from_db()
        assert card_a1.status == "lost"


@pytest.mark.django_db
class TestResetPin:
    def test_admin_resets_pin(self, school_admin_a, card_a1):
        before = card_a1.updated_at
        r = client_for(school_admin_a).post(f"/api/v1/cards/{card_a1.pk}/reset-pin/", {"pin": "9876"}, format="json")
        assert r.status_code == 200 and "pin_hash" not in r.data
        card_a1.refresh_from_db()
        assert check_password("9876", card_a1.pin_hash)
        assert card_a1.updated_at > before  # reaches POS caches via ?since=

    def test_other_school_admin_cannot(self, school_admin_b, card_a1):
        r = client_for(school_admin_b).post(f"/api/v1/cards/{card_a1.pk}/reset-pin/", {"pin": "9876"}, format="json")
        assert r.status_code in (403, 404)

    def test_parent_cannot(self, parent_user, guardian_link_a1, card_a1):
        r = client_for(parent_user).post(f"/api/v1/cards/{card_a1.pk}/reset-pin/", {"pin": "9876"}, format="json")
        assert r.status_code == 403

    def test_bad_pin_and_lost_card(self, school_admin_a, card_a1):
        c = client_for(school_admin_a)
        assert c.post(f"/api/v1/cards/{card_a1.pk}/reset-pin/", {"pin": "12"}, format="json").status_code == 400
        Card.objects.filter(pk=card_a1.pk).update(status="lost")
        assert c.post(f"/api/v1/cards/{card_a1.pk}/reset-pin/", {"pin": "1234"}, format="json").status_code == 409


@pytest.mark.django_db
def test_card_list_filters(school_admin_a, card_a1, student_a2, school_admin_b):
    from cards.services import issue_card

    issue_card(student_a2, "1234", card_uid="04a22b7c")
    c = client_for(school_admin_a)
    assert c.get("/api/v1/cards/", {"card_uid": "04:A2:2B:7C"}).data["count"] == 1
    assert c.get("/api/v1/cards/", {"student": card_a1.student_id}).data["results"][0]["student_name"]
    assert client_for(school_admin_b).get("/api/v1/cards/", {"card_uid": "04a22b7c"}).data["count"] == 0

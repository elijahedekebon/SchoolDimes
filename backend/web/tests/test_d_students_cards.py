"""Section D: students (+tabs), guardians & KYC, cards (issue → freeze → POS cache)."""
import pytest

from accounts.models import GuardianVerification, User
from cards.models import Card
from students.models import Guardian, Student

from .conftest import hx

pytestmark = pytest.mark.django_db

TABS = ("overview", "guardians", "cards", "ledger", "p2p", "attendance", "disputes", "portal")


def test_students_list_filters_and_isolation(admin_a_web, student_a1, student_a2, student_b1):
    body = admin_a_web.get("/school/students").content.decode()
    assert student_a1.name in body and student_b1.name not in body
    region = admin_a_web.get("/school/students", {"search": "Brian"}, **hx("students_table")).content.decode()
    assert student_a2.name in region and student_a1.name not in region


def test_create_and_edit_student(admin_a_web, school_a):
    r = admin_a_web.post("/school/students/new", {"name": "", "class_name": ""}, **hx())
    assert "Name is required" in r.content.decode() and "Class is required" in r.content.decode()
    r = admin_a_web.post("/school/students/new", {"name": "Zed Ochieng", "class_name": "P3"}, **hx())
    s = Student.objects.get(name="Zed Ochieng")
    assert s.school == school_a and r["HX-Redirect"] == f"/school/students/{s.pk}"
    assert s.wallets.filter(wallet_type__in=["main", "savings"]).count() == 2
    admin_a_web.post(f"/school/students/{s.pk}/edit", {"name": "Zed O.", "class_name": "P4", "date_of_birth": "2016-01-02"}, **hx())
    s.refresh_from_db()
    assert (s.name, s.class_name, str(s.date_of_birth)) == ("Zed O.", "P4", "2016-01-02")


def test_student_detail_every_tab_renders(admin_a_web, pos_a):
    sid = pos_a["student"].pk
    assert admin_a_web.get(f"/school/students/{sid}").status_code == 200
    for tab in TABS:
        r = admin_a_web.get(f"/school/students/{sid}", {"tab": tab}, **hx("student_tab"))
        assert r.status_code == 200 and 'data-testid="error-alert"' not in r.content.decode(), tab
    ledger = admin_a_web.get(f"/school/students/{sid}", {"tab": "ledger"}, **hx("student_tab")).content.decode()
    assert "pos purchase" in ledger


def test_student_views_are_tenant_scoped(admin_a_web, student_b1, school_admin_b):
    from cards.services import issue_card

    card = issue_card(student_b1, "1234")
    for url in (f"/school/students/{student_b1.pk}", f"/school/students/{student_b1.pk}/edit",
                f"/school/students/{student_b1.pk}/portal/create", f"/school/cards/{card.pk}/freeze",
                f"/school/cards/{card.pk}/reset-pin", f"/school/cards/issue?student={student_b1.pk}"):
        assert admin_a_web.get(url, **hx()).status_code == 404, url
    assert admin_a_web.post(f"/school/cards/{card.pk}/freeze", **hx()).status_code == 404
    card.refresh_from_db()
    assert card.status == "active"


def test_issue_freeze_and_pos_cache(admin_a_web, school_admin_a, school_a, student_a1):
    from pos.services import build_cache, register_device

    r = admin_a_web.post("/school/cards/issue", {"student": student_a1.pk, "card_uid": "04:A2:2B:7C:91:3E:80",
                                                 "pin": "2468", "pin2": "2469"}, **hx())
    assert "PINs don&#x27;t match" in r.content.decode() or "PINs don't match" in r.content.decode()
    assert admin_a_web.post("/school/cards/issue", {"student": student_a1.pk, "card_uid": "zz", "pin": "2468",
                                                    "pin2": "2468"}, **hx()).content.decode().count("Must be 4")
    r = admin_a_web.post("/school/cards/issue", {"student": student_a1.pk, "card_uid": "04:A2:2B:7C:91:3E:80",
                                                 "pin": "2468", "pin2": "2468"}, **hx())
    assert "Card issued" in r["HX-Trigger"]
    card = Card.objects.get(card_uid="04a22b7c913e80")
    assert card.student == student_a1 and card.pin_hash != "2468"
    admin_a_web.post(f"/school/cards/{card.pk}/freeze", **hx())
    card.refresh_from_db()
    assert card.status == "frozen"
    device, _ = register_device(school_admin_a, school=school_a, device_name="Till", device_role="canteen")
    cached = {c["card_uid"]: c for c in build_cache(device)["cards"]}
    assert cached["04a22b7c913e80"]["status"] == "frozen"
    page = admin_a_web.get(f"/school/students/{student_a1.pk}", {"tab": "cards"}, **hx("student_tab")).content.decode()
    assert "Unfreeze" in page and "pin_hash" not in page and card.pin_hash not in page


def test_reset_pin_mark_lost_and_reissue(admin_a_web, card_a1):
    old_hash = card_a1.pin_hash
    admin_a_web.post(f"/school/cards/{card_a1.pk}/reset-pin", {"pin": "9999", "pin2": "9999"}, **hx())
    card_a1.refresh_from_db()
    assert card_a1.pin_hash != old_hash
    admin_a_web.post(f"/school/cards/{card_a1.pk}/mark-lost", **hx())
    card_a1.refresh_from_db()
    assert card_a1.status == "lost"
    body = admin_a_web.post(f"/school/cards/{card_a1.pk}/unfreeze", **hx()).content.decode()
    assert "card_lost" in body
    admin_a_web.post(f"/school/cards/{card_a1.pk}/reissue", {"pin": "1357", "pin2": "1357"}, **hx())
    assert Card.objects.filter(student=card_a1.student, status="active").count() == 1


def test_uid_preview_uses_server_normalisation(admin_a_web):
    body = admin_a_web.get("/school/cards/uid-preview", {"card_uid": "04 A2-2B:7C"}, **hx()).content.decode()
    assert "04a22b7c" in body


def test_cards_page_find_by_uid(admin_a_web, card_a1, student_b1):
    from cards.services import issue_card

    issue_card(student_b1, "1234", card_uid="04bb22cc")
    body = admin_a_web.get("/school/cards").content.decode()
    assert card_a1.card_uid in body and "04bb22cc" not in body
    r = admin_a_web.get("/school/cards", {"card_uid": "04:BB:22:CC"}, **hx("cards_table")).content.decode()
    assert "04bb22cc" not in r


def test_link_and_unlink_guardian(admin_a_web, student_a1, parent_user):
    body = admin_a_web.get(f"/school/students/{student_a1.pk}/guardian-lookup", {"email": "nobody@x.test"}, **hx())
    assert "No parent account with that email." in body.content.decode()
    body = admin_a_web.get(f"/school/students/{student_a1.pk}/guardian-lookup", {"email": parent_user.email}, **hx())
    assert parent_user.email in body.content.decode()
    admin_a_web.post(f"/school/students/{student_a1.pk}/link-guardian",
                     {"email": parent_user.email, "relationship": "mother"}, **hx())
    link = Guardian.objects.get(parent=parent_user, student=student_a1)
    assert link.relationship == "mother"
    admin_a_web.post(f"/school/guardians/{link.pk}/unlink", **hx())
    assert not Guardian.objects.filter(pk=link.pk).exists()


def test_kyc_review_and_isolation(admin_a_web, admin_b_web, guardian_link_a1, parent_user):
    v = GuardianVerification.objects.create(parent=parent_user, full_name="P", id_document_type="national_id",
                                            id_number="CF1")
    assert "CF1" in admin_a_web.get("/school/guardians").content.decode()
    assert "CF1" not in admin_b_web.get("/school/guardians").content.decode()
    assert admin_b_web.get(f"/school/guardians/kyc/{v.pk}/review", **hx()).status_code == 404
    admin_a_web.post(f"/school/guardians/kyc/{v.pk}/review", {"status": "verified", "review_notes": "seen"}, **hx())
    v.refresh_from_db()
    assert v.status == "verified" and v.review_notes == "seen"


def test_portal_login_create_and_remove(admin_a_web, student_a1):
    body = admin_a_web.post(f"/school/students/{student_a1.pk}/portal/create", {"email": "s@x.test", "password": "short"}, **hx())
    assert "at least 8 characters" in body.content.decode()
    admin_a_web.post(f"/school/students/{student_a1.pk}/portal/create", {"email": "s@x.test", "password": "longenough"}, **hx())
    assert User.objects.get(email="s@x.test").role == "student"
    admin_a_web.post(f"/school/students/{student_a1.pk}/portal/remove", **hx())
    assert not User.objects.filter(email="s@x.test").exists()


def test_overview_tab_with_an_override_set_by_nobody(admin_a_web, student_a1):
    from policies.models import Policy

    Policy.objects.create(school=student_a1.school, student=student_a1, daily_spend_cap="1000")
    body = admin_a_web.get(f"/school/students/{student_a1.pk}").content.decode()
    assert "Student override last set by — (—)" in body

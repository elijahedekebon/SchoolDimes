from decimal import Decimal

import pytest

from accounts.models import GuardianVerification
from conftest import assert_books_balanced, client_for
from privacy.models import DataRequest
from students.models import Guardian, Student
from wallets.models import LedgerEntry, Wallet
from wallets.services import ensure_student_wallets, get_student_wallet, get_system_wallet, post_transfer


@pytest.mark.django_db
class TestMyData:
    def test_contains_own_students_and_ledger_never_pin_hash(self, parent_client, funded_student_a1, student_a2, parent_user):
        GuardianVerification.objects.create(parent=parent_user, full_name="Jane", id_number="CM1")
        data = parent_client.get("/api/v1/privacy/my-data/").data
        assert data["profile"]["email"] == parent_user.email
        assert data["guardian_verification"]["id_number"] == "CM1"
        assert [s["id"] for s in data["students"]] == [funded_student_a1.pk]  # not student_a2
        student = data["students"][0]
        main = next(w for w in student["wallets"] if w["wallet_type"] == "main")
        assert main["balance"] == "10000.00" and main["ledger"][0]["entry_type"] == "deposit"
        text = str(data)
        assert "pin_hash" not in text and funded_student_a1.cards.get().pin_hash not in text
        assert "aggregator_clearing" not in text

    def test_csv_download(self, parent_client, funded_student_a1):
        resp = parent_client.get("/api/v1/privacy/my-data/?format=csv")
        assert resp.status_code == 200 and resp["Content-Type"].startswith("text/csv")
        body = resp.content.decode()
        assert "attachment" in resp["Content-Disposition"]
        assert "ledger:main" in body and "deposit" in body and "pin" not in body.lower().replace("pending", "")

    def test_parents_only(self, admin_a_client):
        assert admin_a_client.get("/api/v1/privacy/my-data/").status_code == 403


@pytest.mark.django_db
class TestDataRequests:
    def request(self, client, **body):
        return client.post("/api/v1/privacy/data-requests/", body, format="json")

    def test_student_deletion_redacts_but_keeps_ledger(self, parent_client, admin_a_client, funded_student_a1, school_a, parent_user):
        # empty the wallet first (deletion refuses while money is held)
        main = get_student_wallet(funded_student_a1)
        resp = self.request(parent_client, request_type="deletion", subject="student", student=funded_student_a1.pk, details="Leaving school")
        assert resp.status_code == 201 and "Financial records" in resp.data["retention_notice"]
        blocked = admin_a_client.post(f"/api/v1/privacy/data-requests/{resp.data['id']}/handle/", {"status": "completed"}, format="json")
        assert blocked.status_code == 409 and blocked.data["code"] == "balance_not_zero"
        post_transfer(debit_wallet=main, credit_wallet=get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT),
                      amount=Decimal("10000"), entry_type="pos_purchase", reference_id="t:1")
        entries_before = LedgerEntry.objects.count()
        done = admin_a_client.post(f"/api/v1/privacy/data-requests/{resp.data['id']}/handle/", {"status": "completed", "notes": "Done"}, format="json")
        assert done.status_code == 200 and "Financial records" in done.data["notes"]
        funded_student_a1.refresh_from_db()
        assert funded_student_a1.name.startswith("Redacted") and funded_student_a1.date_of_birth is None
        assert funded_student_a1.cards.get().status == "lost"
        assert LedgerEntry.objects.count() == entries_before  # nothing deleted
        assert_books_balanced(school_a)

    def test_self_deletion_deactivates_account(self, parent_client, admin_a_client, funded_student_a1, parent_user, other_parent):
        Guardian.objects.create(parent=other_parent, student=funded_student_a1)  # child has another guardian
        GuardianVerification.objects.create(parent=parent_user, full_name="Jane", id_number="CM1")
        resp = self.request(parent_client, request_type="deletion", subject="self")
        admin_a_client.post(f"/api/v1/privacy/data-requests/{resp.data['id']}/handle/", {"status": "completed"}, format="json")
        parent_user.refresh_from_db()
        assert not parent_user.is_active and parent_user.email.endswith("@redacted.invalid")
        assert parent_user.full_name == "" and not parent_user.has_usable_password()
        assert GuardianVerification.objects.get(parent=parent_user).id_number == "REDACTED"
        funded_student_a1.refresh_from_db()
        assert not funded_student_a1.name.startswith("Redacted")  # still has a guardian
        assert LedgerEntry.objects.filter(wallet__student=funded_student_a1).exists()

    def test_scoping_and_permissions(self, parent_client, admin_a_client, admin_b_client, funded_student_a1, student_a2, other_parent, parent_user):
        assert self.request(parent_client, request_type="export", subject="student", student=student_a2.pk).status_code == 404
        resp = self.request(parent_client, request_type="correction", subject="student", student=funded_student_a1.pk, details="DOB wrong")
        rid = resp.data["id"]
        assert admin_a_client.get("/api/v1/privacy/data-requests/").data["count"] == 1
        assert admin_b_client.get("/api/v1/privacy/data-requests/").data["count"] == 0
        assert admin_b_client.post(f"/api/v1/privacy/data-requests/{rid}/handle/", {"status": "completed"}, format="json").status_code == 404
        assert client_for(other_parent).get("/api/v1/privacy/data-requests/").data["count"] == 0
        assert parent_client.post(f"/api/v1/privacy/data-requests/{rid}/handle/", {"status": "completed"}, format="json").status_code == 403
        ok = admin_a_client.post(f"/api/v1/privacy/data-requests/{rid}/handle/", {"status": "in_progress"}, format="json")
        assert ok.data["status"] == "in_progress"
        from notifications.models import NotificationEvent

        assert NotificationEvent.objects.filter(user=parent_user, event_type="data_request_updated").exists()

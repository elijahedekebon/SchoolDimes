from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

import pytest
from freezegun import freeze_time

from conftest import assert_books_balanced, client_for
from notifications.models import NotificationEvent
from payments.aggregator_client import MockAggregatorClient
from payments.models import Deposit, GiftVoucher, RecurringTopUp, StudentTopUpLink, UnmatchedWebhook
from payments.services import expire_stale_deposits, mock_confirm, run_due_recurring_topups
from wallets.models import LedgerEntry, Wallet
from wallets.services import ensure_student_wallets

KAMPALA = ZoneInfo("Africa/Kampala")
WEBHOOK = "/api/v1/payments/webhook/"


def post_webhook(api_client, deposit, *, success=True, amount=None, reference=None, headers=None):
    raw, signed = MockAggregatorClient.build_webhook(
        reference=reference or deposit.reference,
        aggregator_ref=deposit.aggregator_ref if deposit else "",
        amount=amount if amount is not None else (deposit.amount if deposit else "1"),
        success=success,
    )
    hdrs = headers if headers is not None else signed
    return api_client.post(
        WEBHOOK, raw, content_type="application/json",
        **{f"HTTP_{k.upper().replace('-', '_')}": v for k, v in hdrs.items()},
    )


@pytest.fixture
def wallets_a1(student_a1, guardian_link_a1):
    return ensure_student_wallets(student_a1)


def create_deposit(client, wallet, key="k-1", amount="5000", phone="0772000111"):
    return client.post("/api/v1/payments/deposits/", {
        "wallet": wallet.pk, "amount": amount, "channel": "momo",
        "payer_phone": phone, "idempotency_key": key,
    }, format="json")


@pytest.mark.django_db
class TestDeposits:
    def test_initiation_moves_no_money(self, parent_client, wallets_a1):
        main, _ = wallets_a1
        resp = create_deposit(parent_client, main)
        assert resp.status_code == 201, resp.data
        assert resp.data["status"] == "pending"
        assert resp.data["instructions"]["type"] == "momo_prompt"
        assert resp.data["reference"].startswith("SD-DEP-")
        main.refresh_from_db()
        assert main.balance == 0
        assert LedgerEntry.objects.count() == 0

    def test_confirmed_webhook_credits_once(self, parent_client, api_client, wallets_a1, school_a, parent_user):
        main, _ = wallets_a1
        deposit = Deposit.objects.get(pk=create_deposit(parent_client, main).data["id"])
        resp = post_webhook(api_client, deposit)
        assert resp.status_code == 200 and resp.data["status"] == "confirmed"
        main.refresh_from_db()
        assert main.balance == Decimal("5000.00")
        assert_books_balanced(school_a)
        assert NotificationEvent.objects.filter(user=parent_user, event_type="deposit_confirmed").count() == 1

        replay = post_webhook(api_client, deposit)
        assert replay.status_code == 200 and replay.data["status"] == "duplicate"
        main.refresh_from_db()
        assert main.balance == Decimal("5000.00")
        assert NotificationEvent.objects.filter(user=parent_user, event_type="deposit_confirmed").count() == 1

    def test_bad_signature_rejected(self, parent_client, api_client, wallets_a1):
        main, _ = wallets_a1
        deposit = Deposit.objects.get(pk=create_deposit(parent_client, main).data["id"])
        resp = post_webhook(api_client, deposit, headers={"X-SchoolDimes-Signature": "deadbeef"})
        assert resp.status_code == 401
        resp = post_webhook(api_client, deposit, headers={})
        assert resp.status_code == 401
        deposit.refresh_from_db()
        assert deposit.status == "pending" and LedgerEntry.objects.count() == 0

    def test_failed_payment_moves_no_money_and_notifies(self, parent_client, api_client, wallets_a1, parent_user):
        main, _ = wallets_a1
        deposit = Deposit.objects.get(pk=create_deposit(parent_client, main).data["id"])
        resp = post_webhook(api_client, deposit, success=False)
        assert resp.data["status"] == "failed"
        deposit.refresh_from_db()
        assert deposit.status == "failed" and LedgerEntry.objects.count() == 0
        assert NotificationEvent.objects.filter(user=parent_user, event_type="deposit_failed").exists()
        # a later success for a failed deposit is parked for review, not credited
        assert post_webhook(api_client, deposit).data["status"] == "unmatched"
        assert LedgerEntry.objects.count() == 0

    def test_unknown_reference_logged_and_acknowledged(self, api_client):
        raw, headers = MockAggregatorClient.build_webhook(reference="SD-DEP-NOPE", amount="10")
        resp = api_client.post(WEBHOOK, raw, content_type="application/json",
                               HTTP_X_SCHOOLDIMES_SIGNATURE=headers["X-SchoolDimes-Signature"])
        assert resp.status_code == 200 and resp.data["status"] == "unmatched"
        assert UnmatchedWebhook.objects.filter(reference="SD-DEP-NOPE", reason="unknown_reference").exists()

    def test_amount_mismatch_not_credited(self, parent_client, api_client, wallets_a1):
        main, _ = wallets_a1
        deposit = Deposit.objects.get(pk=create_deposit(parent_client, main).data["id"])
        assert post_webhook(api_client, deposit, amount="9999").data["status"] == "unmatched"
        assert LedgerEntry.objects.count() == 0

    def test_idempotent_initiation(self, parent_client, wallets_a1):
        main, _ = wallets_a1
        first = create_deposit(parent_client, main, key="same")
        again = create_deposit(parent_client, main, key="same")
        assert again.status_code == 200 and again.data["id"] == first.data["id"]
        conflict = create_deposit(parent_client, main, key="same", amount="7000")
        assert conflict.status_code == 409 and conflict.data["code"] == "idempotency_conflict"
        assert Deposit.objects.count() == 1

    def test_amount_validation(self, parent_client, wallets_a1):
        main, _ = wallets_a1
        assert create_deposit(parent_client, main, key="a", amount="0").status_code in (400, 422)
        assert create_deposit(parent_client, main, key="b", amount="-10").status_code in (400, 422)
        resp = create_deposit(parent_client, main, key="c", amount="999999999")
        assert resp.status_code == 400 and resp.data["code"] == "amount_too_large"

    def test_cannot_top_up_unlinked_student(self, wallets_a1, other_parent):
        main, _ = wallets_a1
        resp = create_deposit(client_for(other_parent), main)
        assert resp.status_code == 404

    def test_declined_at_initiation(self, parent_client, wallets_a1):
        main, _ = wallets_a1
        resp = create_deposit(parent_client, main, phone="0772000999")
        assert resp.data["status"] == "failed" and resp.data["failure_reason"] == "declined"

    def test_history_is_scoped_and_filterable(self, parent_client, wallets_a1, other_parent, student_a2, admin_b_client):
        main, _ = wallets_a1
        create_deposit(parent_client, main)
        assert len(parent_client.get("/api/v1/payments/deposits/").data["results"]) == 1
        assert len(parent_client.get(f"/api/v1/payments/deposits/?student={student_a2.pk}").data["results"]) == 0
        assert client_for(other_parent).get("/api/v1/payments/deposits/").data["results"] == []
        assert admin_b_client.get("/api/v1/payments/deposits/").data["results"] == []

    def test_polling_other_parents_deposit_is_404(self, parent_client, wallets_a1, other_parent):
        main, _ = wallets_a1
        dep_id = create_deposit(parent_client, main).data["id"]
        assert parent_client.get(f"/api/v1/payments/deposits/{dep_id}/").status_code == 200
        assert client_for(other_parent).get(f"/api/v1/payments/deposits/{dep_id}/").status_code == 404

    def test_stale_deposits_expire_and_late_success_still_credits(self, parent_client, wallets_a1):
        main, _ = wallets_a1
        with freeze_time("2026-03-02 06:00:00"):
            deposit = Deposit.objects.get(pk=create_deposit(parent_client, main).data["id"])
        with freeze_time("2026-03-04 06:00:00"):
            assert expire_stale_deposits() == 1
        deposit.refresh_from_db()
        assert deposit.status == "expired"
        assert mock_confirm(deposit) == "confirmed"
        main.refresh_from_db()
        assert main.balance == Decimal("5000.00")


@pytest.mark.django_db
class TestContributorLinks:
    def make_link(self, parent_client, student):
        resp = parent_client.post("/api/v1/payments/topup-links/", {"student": student.pk}, format="json")
        assert resp.status_code == 201, resp.data
        return resp.data

    def test_public_view_exposes_only_first_name_and_school(self, parent_client, api_client, wallets_a1, student_a1):
        link = self.make_link(parent_client, student_a1)
        assert link["share_url"].endswith(link["token"])
        resp = api_client.get(f"/api/v1/public/topup-links/{link['token']}/")
        assert resp.status_code == 200
        assert resp.data == {"student_first_name": "Amina", "school_name": student_a1.school.name}

    def test_contributor_deposit_notifies_guardians(self, parent_client, api_client, wallets_a1, student_a1, parent_user, school_a):
        link = self.make_link(parent_client, student_a1)
        resp = api_client.post(f"/api/v1/public/topup-links/{link['token']}/deposits/", {
            "contributor": {"name": "Jjajja Nalongo", "phone_number": "0701000222", "relationship_label": "Grandmother"},
            "amount": "3000", "channel": "ussd", "idempotency_key": "contrib-1",
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert "wallet" not in resp.data and "student" not in resp.data
        assert resp.data["instructions"]["type"] == "ussd"
        deposit = Deposit.objects.get(reference=resp.data["reference"])
        assert deposit.contributor.name == "Jjajja Nalongo"
        mock_confirm(deposit)
        wallets_a1[0].refresh_from_db()
        assert wallets_a1[0].balance == Decimal("3000.00")
        event = NotificationEvent.objects.get(user=parent_user, event_type="contributor_topup_received")
        assert "Jjajja Nalongo" in event.body
        replay = api_client.post(f"/api/v1/public/topup-links/{link['token']}/deposits/", {
            "contributor": {"name": "Jjajja Nalongo", "phone_number": "0701000222"},
            "amount": "3000", "channel": "ussd", "idempotency_key": "contrib-1",
        }, format="json")
        assert replay.status_code == 200 and replay.data["reference"] == deposit.reference
        from payments.models import Contributor
        assert Contributor.objects.count() == 1
        status = api_client.get(f"/api/v1/public/topup-links/{link['token']}/deposits/{deposit.reference}/")
        assert status.data["status"] == "confirmed"
        assert_books_balanced(school_a)

    def test_revoked_link_is_dead(self, parent_client, api_client, wallets_a1, student_a1):
        link = self.make_link(parent_client, student_a1)
        assert parent_client.post(f"/api/v1/payments/topup-links/{link['id']}/revoke/").status_code == 200
        assert api_client.get(f"/api/v1/public/topup-links/{link['token']}/").status_code == 404
        resp = api_client.post(f"/api/v1/public/topup-links/{link['token']}/deposits/", {
            "contributor": {"name": "X", "phone_number": "1"}, "amount": "10", "channel": "momo", "idempotency_key": "r",
        }, format="json")
        assert resp.status_code == 404

    def test_unknown_token_404(self, api_client, db):
        assert api_client.get("/api/v1/public/topup-links/not-a-token/").status_code == 404

    def test_other_parent_cannot_create_link(self, student_a1, other_parent, wallets_a1):
        resp = client_for(other_parent).post("/api/v1/payments/topup-links/", {"student": student_a1.pk}, format="json")
        assert resp.status_code == 404
        assert not StudentTopUpLink.objects.exists()

    def test_throttling(self, settings, parent_client, api_client, wallets_a1, student_a1):
        settings.PUBLIC_TOPUP_THROTTLE_RATE = "3/min"
        link = self.make_link(parent_client, student_a1)
        codes = [api_client.get(f"/api/v1/public/topup-links/{link['token']}/").status_code for _ in range(5)]
        assert codes[:3] == [200, 200, 200] and codes[3] == 429


@pytest.mark.django_db
class TestGiftVouchers:
    def test_parent_voucher_paid_credits_and_notifies_with_message(self, parent_client, wallets_a1, student_a1, parent_user, school_a):
        resp = parent_client.post("/api/v1/payments/gift-vouchers/", {
            "student": student_a1.pk, "amount": "2500", "message": "Happy birthday!",
            "channel": "momo", "payer_phone": "0772000111", "idempotency_key": "gv-1",
        }, format="json")
        assert resp.status_code == 201, resp.data
        assert resp.data["status"] == "pending_payment"
        voucher = GiftVoucher.objects.get(pk=resp.data["id"])
        assert voucher.deposit.reference.startswith("SD-GV-")
        mock_confirm(voucher.deposit)
        voucher.refresh_from_db()
        assert voucher.status == "redeemed" and voucher.redeemed_at
        main = wallets_a1[0]
        main.refresh_from_db()
        assert main.balance == Decimal("2500.00")
        assert main.ledger_entries.get().entry_type == "gift_voucher"
        event = NotificationEvent.objects.get(user=parent_user, event_type="gift_received")
        assert "Happy birthday!" in event.body
        assert_books_balanced(school_a)

    def test_public_voucher_from_contributor(self, parent_client, api_client, wallets_a1, student_a1):
        token = parent_client.post("/api/v1/payments/topup-links/", {"student": student_a1.pk}, format="json").data["token"]
        resp = api_client.post(f"/api/v1/public/topup-links/{token}/gift-vouchers/", {
            "contributor": {"name": "Uncle Tom", "email": "tom@example.com"},
            "amount": "1000", "message": "Buy a book", "channel": "bank", "idempotency_key": "gv-pub",
        }, format="json")
        assert resp.status_code == 201, resp.data
        voucher = GiftVoucher.objects.get()
        assert voucher.sender_name == "Uncle Tom"
        mock_confirm(voucher.deposit)
        voucher.refresh_from_db()
        assert voucher.status == "redeemed"

    def test_failed_voucher_payment_cancels(self, parent_client, wallets_a1, student_a1):
        resp = parent_client.post("/api/v1/payments/gift-vouchers/", {
            "student": student_a1.pk, "amount": "2500", "channel": "momo",
            "payer_phone": "0772000111", "idempotency_key": "gv-2",
        }, format="json")
        voucher = GiftVoucher.objects.get(pk=resp.data["id"])
        mock_confirm(voucher.deposit, success=False)
        voucher.refresh_from_db()
        assert voucher.status == "cancelled" and LedgerEntry.objects.count() == 0


def kampala(*args):
    return datetime(*args, tzinfo=KAMPALA)


@pytest.mark.django_db
class TestRecurringTopUps:
    def create(self, parent_client, student, phone="0772000111"):
        resp = parent_client.post("/api/v1/payments/recurring-topups/", {
            "student": student.pk, "amount": "4000", "channel": "momo", "payer_phone": phone,
            "frequency": "weekly", "day_of_week": 0,
        }, format="json")
        assert resp.status_code == 201, resp.data
        return RecurringTopUp.objects.get(pk=resp.data["id"])

    def test_fires_on_schedule_once(self, parent_client, wallets_a1, student_a1, parent_user, school_a):
        with freeze_time(kampala(2026, 3, 2, 7, 0)):  # Monday 07:00 Kampala
            rt = self.create(parent_client, student_a1)
            assert rt.next_run_at == kampala(2026, 3, 2, 8, 0)
        with freeze_time(kampala(2026, 3, 2, 7, 59)):
            assert run_due_recurring_topups() == []
        with freeze_time(kampala(2026, 3, 2, 8, 1)):
            results = run_due_recurring_topups()
            assert [r["outcome"] for r in results] == ["confirmed"]
            assert run_due_recurring_topups() == []  # Beat fires twice -> nothing
        main = wallets_a1[0]
        main.refresh_from_db()
        assert main.balance == Decimal("4000.00")
        rt.refresh_from_db()
        assert rt.next_run_at == kampala(2026, 3, 9, 8, 0) and rt.last_status == "succeeded"
        assert NotificationEvent.objects.filter(user=parent_user, event_type="recurring_topup_executed").count() == 1
        assert_books_balanced(school_a)

    def test_same_window_cannot_double_top_up(self, parent_client, wallets_a1, student_a1):
        with freeze_time(kampala(2026, 3, 2, 7, 0)):
            rt = self.create(parent_client, student_a1)
        # simulate a second worker that already ran this window
        scheduled = rt.next_run_at
        with freeze_time(kampala(2026, 3, 2, 8, 1)):
            run_due_recurring_topups()
            RecurringTopUp.objects.filter(pk=rt.pk).update(next_run_at=scheduled)  # stale view of the row
            results = run_due_recurring_topups()
        assert results[0]["outcome"] == "skipped_duplicate_window"
        assert Deposit.objects.count() == 1

    def test_auto_pause_after_repeated_failures(self, settings, parent_client, wallets_a1, student_a1, parent_user):
        settings.RECURRING_TOPUP_MAX_FAILURES = 3
        with freeze_time(kampala(2026, 3, 2, 7, 0)):
            rt = self.create(parent_client, student_a1, phone="0772000999")  # mock declines
        for day in (2, 9, 16):
            with freeze_time(kampala(2026, 3, day, 8, 5)):
                run_due_recurring_topups()
        rt.refresh_from_db()
        assert rt.active is False and rt.consecutive_failures == 3
        assert NotificationEvent.objects.filter(user=parent_user, event_type="recurring_topup_failed").count() == 3
        assert NotificationEvent.objects.filter(user=parent_user, event_type="recurring_topup_paused").count() == 1
        with freeze_time(kampala(2026, 3, 23, 8, 5)):
            assert run_due_recurring_topups() == []
        assert LedgerEntry.objects.count() == 0

    def test_monthly_schedule_and_validation(self, parent_client, wallets_a1, student_a1):
        with freeze_time(kampala(2026, 1, 31, 12, 0)):
            resp = parent_client.post("/api/v1/payments/recurring-topups/", {
                "student": student_a1.pk, "amount": "4000", "payer_phone": "0772",
                "frequency": "monthly", "day_of_month": 5,
            }, format="json")
            assert resp.status_code == 201
            assert RecurringTopUp.objects.get().next_run_at == kampala(2026, 2, 5, 8, 0)
            bad = parent_client.post("/api/v1/payments/recurring-topups/", {
                "student": student_a1.pk, "amount": "4000", "payer_phone": "0772",
                "frequency": "monthly", "day_of_month": 31,
            }, format="json")
            assert bad.status_code == 400 and bad.data["code"] == "schedule_invalid"

    def test_only_own_students(self, wallets_a1, student_a1, other_parent):
        resp = client_for(other_parent).post("/api/v1/payments/recurring-topups/", {
            "student": student_a1.pk, "amount": "4000", "payer_phone": "0772",
            "frequency": "weekly", "day_of_week": 1,
        }, format="json")
        assert resp.status_code == 404

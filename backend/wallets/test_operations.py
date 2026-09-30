"""Section C: savings, withdrawals, P2P, pattern alerts, card freeze."""
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from cards.services import issue_card
from conftest import assert_books_balanced, client_for, fund_wallet
from notifications.models import NotificationEvent
from policies.services import get_school_policy
from students.models import Guardian, Student
from wallets.models import LedgerEntry, P2PAlert, SavingsGoal, Wallet
from wallets.services import ensure_student_wallets, get_student_wallet


def wallets(student):
    return get_student_wallet(student, "main"), get_student_wallet(student, "savings")


@pytest.mark.django_db
class TestSavings:
    def test_move_in_and_out(self, parent_client, funded_student_a1, school_a):
        main, savings = wallets(funded_student_a1)
        resp = parent_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "4000"}, format="json")
        assert resp.status_code == 200, resp.data
        assert resp.data["main"]["balance"] == "6000.00" and resp.data["savings"]["balance"] == "4000.00"
        resp = parent_client.post(f"/api/v1/wallets/{savings.pk}/savings/move-out/", {"amount": "1500"}, format="json")
        assert resp.data["main"]["balance"] == "7500.00" and resp.data["savings"]["balance"] == "2500.00"
        types = set(LedgerEntry.objects.filter(wallet=savings).values_list("direction", "entry_type"))
        assert types == {("credit", "savings_move_in"), ("debit", "savings_move_out")}
        too_much = parent_client.post(f"/api/v1/wallets/{savings.pk}/savings/move-out/", {"amount": "9999"}, format="json")
        assert too_much.status_code == 422 and too_much.data["code"] == "insufficient_funds"
        assert_books_balanced(school_a)

    def test_goal_progress_and_reached_notification(self, parent_client, funded_student_a1, parent_user):
        main, savings = wallets(funded_student_a1)
        goal = SavingsGoal.objects.create(wallet=savings, goal_name="Football", target_amount=Decimal("5000"))
        parent_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "2500"}, format="json")
        data = parent_client.get(f"/api/v1/savings-goals/{goal.pk}/").data
        assert data["current_amount"] == "2500.00" and data["progress_percent"] == 50.0 and data["is_reached"] is False
        parent_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "3000"}, format="json")
        parent_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "100"}, format="json")
        goal.refresh_from_db()
        assert goal.reached_at is not None
        assert NotificationEvent.objects.filter(user=parent_user, event_type="savings_goal_reached").count() == 1

    def test_withdrawal_window_and_failed_payout_reversal(self, parent_client, funded_student_a1, parent_user, school_a):
        main, savings = wallets(funded_student_a1)
        parent_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "5000"}, format="json")
        closed = parent_client.post(f"/api/v1/wallets/{savings.pk}/savings/withdraw/", {"amount": "1000", "phone_number": "0772"}, format="json")
        assert closed.status_code == 409 and closed.data["code"] == "withdrawal_window_closed"
        now = timezone.now()
        window = parent_client.put(f"/api/v1/wallets/{savings.pk}/savings/withdrawal-window/", {
            "withdrawal_window_start": (now - timedelta(days=1)).isoformat(),
            "withdrawal_window_end": (now + timedelta(days=1)).isoformat(),
        }, format="json")
        assert window.status_code == 200 and window.data["is_open"] is True
        ok = parent_client.post(f"/api/v1/wallets/{savings.pk}/savings/withdraw/", {"amount": "1000", "phone_number": "0772000111"}, format="json")
        assert ok.status_code == 201 and ok.data["status"] == "succeeded"
        failed = parent_client.post(f"/api/v1/wallets/{savings.pk}/savings/withdraw/", {"amount": "1000", "phone_number": "0772000998"}, format="json")
        assert failed.data["status"] == "failed"
        savings.refresh_from_db()
        assert savings.balance == Decimal("4000.00")  # 5000 - 1000; the failed 1000 was reversed
        assert LedgerEntry.objects.filter(wallet=savings, entry_type="reversal", direction="credit").count() == 1
        assert NotificationEvent.objects.filter(user=parent_user, event_type="savings_withdrawal_failed").exists()
        assert_books_balanced(school_a)

    def test_admin_can_move_but_not_withdraw(self, admin_a_client, funded_student_a1):
        main, savings = wallets(funded_student_a1)
        assert admin_a_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "10"}, format="json").status_code == 200
        assert admin_a_client.post(f"/api/v1/wallets/{savings.pk}/savings/withdraw/", {"amount": "1"}, format="json").status_code == 403


@pytest.fixture
def classmate(school_a):
    student = Student.objects.create(school=school_a, name="Brian Okello", class_name="P4")
    ensure_student_wallets(student)
    issue_card(student, "5555")
    return student


def send(client, sender, recipient, amount):
    return client.post("/api/v1/wallets/transfer/", {
        "sender_student": sender.pk, "recipient_student": recipient.pk, "amount": amount,
    }, format="json")


@pytest.mark.django_db
class TestP2P:
    def test_transfer_moves_money_and_notifies(self, parent_client, funded_student_a1, classmate, school_a):
        other_parent_link = Guardian.objects.create(
            parent=type(Guardian.objects.first().parent).objects.create_user(
                email="bp@x.test", password="pw123456", role="parent"),
            student=classmate)
        resp = send(parent_client, funded_student_a1, classmate, "1200")
        assert resp.status_code == 201, resp.data
        main, _ = wallets(classmate)
        assert main.balance == Decimal("1200.00")
        entries = LedgerEntry.objects.filter(reference_id=f"p2p:{resp.data['id']}")
        assert set(entries.values_list("entry_type", flat=True)) == {"p2p_transfer_out", "p2p_transfer_in"}
        assert NotificationEvent.objects.filter(user=other_parent_link.parent, event_type="p2p_transfer_received").exists()
        history = parent_client.get(f"/api/v1/students/{funded_student_a1.pk}/p2p-history/").data
        assert history["count"] == 1 and history["results"][0]["recipient_name"] == "Brian Okello"
        assert_books_balanced(school_a)

    def test_same_school_only(self, parent_client, funded_student_a1, student_b1):
        ensure_student_wallets(student_b1)
        issue_card(student_b1, "1111")
        resp = send(parent_client, funded_student_a1, student_b1, "100")
        assert resp.status_code == 404  # other schools' students are invisible

    def test_daily_cap_disabled_and_frozen(self, parent_client, funded_student_a1, classmate, school_a):
        policy = get_school_policy(school_a)
        policy.p2p_daily_cap = Decimal("2000")
        policy.save()
        assert send(parent_client, funded_student_a1, classmate, "1500").status_code == 201
        capped = send(parent_client, funded_student_a1, classmate, "600")
        assert capped.status_code == 422 and capped.data["code"] == "p2p_cap_exceeded"
        card = funded_student_a1.cards.get()
        card.status = "frozen"
        card.save()
        assert send(parent_client, funded_student_a1, classmate, "10").data["code"] == "card_frozen"
        card.status = "active"
        card.save()
        classmate.cards.update(status="frozen")
        assert send(parent_client, funded_student_a1, classmate, "10").data["code"] == "recipient_card_inactive"
        classmate.cards.update(status="active")
        policy.p2p_enabled = False
        policy.save()
        assert send(parent_client, funded_student_a1, classmate, "10").data["code"] == "p2p_disabled"

    def test_only_senders_guardian_initiates(self, funded_student_a1, classmate, other_parent):
        assert send(client_for(other_parent), funded_student_a1, classmate, "10").status_code == 404

    def test_many_senders_alert(self, settings, school_a, classmate, school_admin_a):
        settings.P2P_ALERT_DISTINCT_SENDERS = 3
        from wallets.p2p import p2p_transfer

        for i in range(4):
            s = Student.objects.create(school=school_a, name=f"Sender {i}", class_name="P4")
            main, _ = ensure_student_wallets(s)
            issue_card(s, "1234")
            fund_wallet(main, "1000")
            p2p_transfer(s, classmate, "200")
        alerts = P2PAlert.objects.filter(student=classmate, rule="many_distinct_senders")
        assert alerts.count() == 1  # one open alert, not one per transfer
        assert NotificationEvent.objects.filter(user=school_admin_a, event_type="p2p_alert_raised").count() == 1
        resp = client_for(school_admin_a).post(f"/api/v1/p2p-alerts/{alerts.get().pk}/review/", {"status": "reviewed", "review_notes": "Spoke to class teacher"}, format="json")
        assert resp.status_code == 200 and resp.data["status"] == "reviewed"

    def test_repeated_near_cap_alert(self, settings, school_a, funded_student_a1, classmate):
        settings.P2P_ALERT_NEAR_CAP_COUNT = 2
        policy = get_school_policy(school_a)
        policy.p2p_daily_cap = Decimal("1000")
        policy.save()
        from wallets.p2p import p2p_transfer

        p2p_transfer(funded_student_a1, classmate, "900")
        assert not P2PAlert.objects.exists()
        p2p_transfer(classmate, funded_student_a1, "100")
        # next day-equivalent: move the first transfer back so the cap resets
        LedgerEntry.objects.filter(entry_type="p2p_transfer_out").update(created_at=timezone.now() - timedelta(days=1))
        p2p_transfer(funded_student_a1, classmate, "850")
        assert P2PAlert.objects.filter(student=funded_student_a1, rule="repeated_near_cap").exists()

    def test_alert_queue_is_tenant_scoped(self, admin_b_client, school_a, classmate):
        alert = P2PAlert.objects.create(school=school_a, student=classmate, rule="many_distinct_senders")
        assert admin_b_client.get("/api/v1/p2p-alerts/").data["results"] == []
        assert admin_b_client.post(f"/api/v1/p2p-alerts/{alert.pk}/review/", {"status": "dismissed"}).status_code == 404


@pytest.mark.django_db
class TestCardFreeze:
    def test_freeze_notifies_other_guardians_and_blocks(self, parent_client, funded_student_a1, other_parent):
        Guardian.objects.create(parent=other_parent, student=funded_student_a1)
        card = funded_student_a1.cards.get()
        resp = parent_client.post(f"/api/v1/cards/{card.pk}/freeze/")
        assert resp.status_code == 200 and resp.data["status"] == "frozen"
        assert NotificationEvent.objects.filter(user=other_parent, event_type="card_frozen").count() == 1
        assert not NotificationEvent.objects.filter(event_type="card_frozen").exclude(user=other_parent).exists()
        main, _ = wallets(funded_student_a1)
        blocked = parent_client.post(f"/api/v1/wallets/{main.pk}/savings/move-in/", {"amount": "10"}, format="json")
        assert blocked.data["code"] == "card_frozen"
        parent_client.post(f"/api/v1/cards/{card.pk}/unfreeze/")
        assert NotificationEvent.objects.filter(user=other_parent, event_type="card_unfrozen").exists()

    def test_report_lost_then_cannot_unfreeze(self, parent_client, admin_a_client, funded_student_a1):
        card = funded_student_a1.cards.get()
        assert parent_client.post(f"/api/v1/cards/{card.pk}/report-lost/").data["status"] == "lost"
        assert parent_client.post(f"/api/v1/cards/{card.pk}/unfreeze/").status_code == 409
        new = admin_a_client.post(f"/api/v1/cards/{card.pk}/reissue/", {"pin": "2468"}, format="json")
        assert new.status_code == 201 and new.data["status"] == "active"

    def test_other_school_admin_cannot_freeze(self, admin_b_client, funded_student_a1):
        card = funded_student_a1.cards.get()
        assert admin_b_client.post(f"/api/v1/cards/{card.pk}/freeze/").status_code == 404

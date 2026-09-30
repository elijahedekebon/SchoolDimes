from decimal import Decimal

import pytest

from conftest import client_for
from notifications.models import DevicePushToken, NotificationEvent
from notifications.services import get_preferences, notify
from policies.services import get_school_policy
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_student_wallet, get_system_wallet, post_transfer


def spend(student, amount, ref):
    wallet = get_student_wallet(student)
    post_transfer(debit_wallet=wallet, credit_wallet=get_system_wallet(student.school_id, Wallet.WalletType.SCHOOL_SETTLEMENT),
                  amount=Decimal(amount), entry_type=LedgerEntry.EntryType.POS_PURCHASE, reference_id=ref)


@pytest.mark.django_db
class TestRendering:
    @pytest.mark.parametrize("language,title", [("en", "Top-up received"), ("sw", "Malipo yamepokelewa"), ("lg", "Ssente zituuse")])
    def test_rendered_in_recipients_language(self, parent_user, language, title):
        parent_user.preferred_language = language
        parent_user.save()
        event = notify(parent_user, "deposit_confirmed", {"amount": "5,000", "student_name": "Amina"})[0]
        assert event.title == title and "5,000" in event.body and "Amina" in event.body

    def test_labels_are_translated_too(self, parent_user):
        parent_user.preferred_language = "sw"
        parent_user.save()
        event = notify(parent_user, "deposit_failed", {"amount": "1", "student_name": "A", "reason": "expired"})[0]
        assert "ombi la malipo limeisha muda" in event.body

    def test_channels_and_stub_backends(self, parent_user):
        parent_user.phone_number = "0772000111"
        parent_user.save()
        pref = get_preferences(parent_user)
        pref.sms_enabled = True
        pref.save()
        DevicePushToken.objects.create(user=parent_user, token="fcm-abc", platform="android")
        events = {e.channel: e for e in notify(parent_user, "card_frozen", {"student_name": "A", "actor_name": "B"})}
        assert set(events) == {"in_app", "sms", "push"}
        assert events["in_app"].status == "sent"
        # SMS/push dispatch on commit; run the task inline as the worker would
        from notifications.tasks import dispatch_notification

        for channel in ("sms", "push"):
            dispatch_notification(events[channel].pk)
            events[channel].refresh_from_db()
            assert events[channel].status == "logged"  # stubs never pretend to deliver


@pytest.mark.django_db
class TestLowBalance:
    def test_crossing_threshold_notifies_once_with_top_up_action(self, funded_student_a1, parent_user, school_a):
        policy = get_school_policy(school_a)
        policy.low_balance_threshold = Decimal("3000")
        policy.save()
        spend(funded_student_a1, "6000", "t:1")   # 10000 -> 4000: above threshold
        assert not NotificationEvent.objects.filter(event_type="low_balance").exists()
        spend(funded_student_a1, "1500", "t:2")   # 4000 -> 2500: crosses
        spend(funded_student_a1, "500", "t:3")    # already below: no new alert
        spend(funded_student_a1, "100", "t:4")
        events = NotificationEvent.objects.filter(user=parent_user, event_type="low_balance")
        assert events.count() == 1
        action = events.get().payload["action"]
        assert action["type"] == "top_up" and action["wallet_id"] == get_student_wallet(funded_student_a1).pk
        assert Decimal(action["suggested_amount"]) >= 1000

    def test_throttle_blocks_repeat_crossings(self, funded_student_a1, parent_user, school_a):
        from conftest import fund_wallet

        pref = get_preferences(parent_user)
        pref.low_balance_thresholds = {str(funded_student_a1.pk): "5000"}
        pref.save()
        spend(funded_student_a1, "6000", "t:1")          # crosses 5000
        fund_wallet(get_student_wallet(funded_student_a1), "6000")
        spend(funded_student_a1, "6000", "t:2")          # crosses again within the throttle window
        assert NotificationEvent.objects.filter(user=parent_user, event_type="low_balance").count() == 1


@pytest.mark.django_db
class TestEndpoints:
    def test_list_read_and_read_all(self, parent_client, parent_user, other_parent):
        for i in range(3):
            notify(parent_user, "card_unfrozen", {"student_name": f"S{i}", "actor_name": "X"})
        mine = notify(other_parent, "card_unfrozen", {"student_name": "Z", "actor_name": "X"})[0]
        data = parent_client.get("/api/v1/notifications/").data
        assert data["count"] == 3 and data["unread_count"] == 3
        first = data["results"][0]["id"]
        assert parent_client.post(f"/api/v1/notifications/{first}/read/").data["read_at"] is not None
        assert parent_client.get("/api/v1/notifications/?unread=true").data["count"] == 2
        assert parent_client.post("/api/v1/notifications/read-all/").data["marked_read"] == 2
        assert parent_client.post(f"/api/v1/notifications/{mine.pk}/read/").status_code == 404

    def test_preferences(self, parent_client, guardian_link_a1, student_a1, student_a2):
        resp = parent_client.put("/api/v1/notifications/preferences/", {
            "in_app_enabled": True, "sms_enabled": True, "push_enabled": False,
            "low_balance_thresholds": {str(student_a1.pk): "2500"}}, format="json")
        assert resp.status_code == 200 and resp.data["low_balance_thresholds"] == {str(student_a1.pk): "2500.00"}
        bad = parent_client.patch("/api/v1/notifications/preferences/", {
            "low_balance_thresholds": {str(student_a2.pk): "1"}}, format="json")
        assert bad.status_code == 400

    def test_push_tokens(self, parent_client, other_parent):
        assert parent_client.post("/api/v1/notifications/push-tokens/", {"token": "tok-1", "platform": "android"}, format="json").status_code == 201
        # same phone, new owner: the token moves
        assert client_for(other_parent).post("/api/v1/notifications/push-tokens/", {"token": "tok-1", "platform": "android"}, format="json").status_code == 200
        assert parent_client.get("/api/v1/notifications/push-tokens/").data["count"] == 0
        assert client_for(other_parent).delete("/api/v1/notifications/push-tokens/tok-1/").status_code == 204
        assert not DevicePushToken.objects.exists()

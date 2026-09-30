import uuid
from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from cards.services import freeze_card, issue_card
from conftest import assert_books_balanced, fund_wallet
from notifications.models import NotificationEvent
from payments.models import Deposit
from payments.services import mock_confirm
from policies.models import Policy, Product, ProductCategory
from pos.models import Device, PinFailureReport, PosTransaction
from pos.services import register_device
from students.models import Student
from tenants.services import get_school_settings
from wallets.models import LedgerEntry, Wallet
from wallets.services import ensure_student_wallets, get_student_wallet, get_system_wallet


def device_client(raw_token):
    client = APIClient()
    client.credentials(HTTP_AUTHORIZATION=f"Device {raw_token}")
    return client


@pytest.fixture
def canteen(school_admin_a, school_a):
    device, raw = register_device(school_admin_a, school=school_a, device_name="Canteen 1", device_role="canteen")
    return device, device_client(raw)


@pytest.fixture
def canteen2(school_admin_a, school_a):
    device, raw = register_device(school_admin_a, school=school_a, device_name="Canteen 2", device_role="canteen")
    return device, device_client(raw)


@pytest.fixture
def catalog(school_a):
    meals = ProductCategory.objects.create(school=school_a, name="Meals")
    sugary = ProductCategory.objects.create(school=school_a, name="Sugary drinks", is_unhealthy=True)
    return {
        "rice": Product.objects.create(school=school_a, name="Rice", category=meals, price=Decimal("3000")),
        "soda": Product.objects.create(school=school_a, name="Soda", category=sugary, price=Decimal("1500")),
    }


def sale(card, amount, items=None, key=None, minutes_ago=5):
    return {
        "idempotency_key": key or str(uuid.uuid4()),
        "card_uid": card.card_uid,
        "amount": str(amount),
        "items": items or [],
        "device_local_timestamp": (timezone.now() - timedelta(minutes=minutes_ago)).isoformat(),
    }


def line(product, qty=1):
    return {"product_id": product.pk, "quantity": qty, "unit_price": str(product.price)}


def sync(client, *txns, pin_failures=None):
    resp = client.post("/api/v1/pos/sync/", {"transactions": list(txns), "pin_failures": pin_failures or []}, format="json")
    assert resp.status_code == 200, resp.data
    return resp.data


@pytest.mark.django_db
class TestDevices:
    def test_register_shows_token_once_and_authenticates(self, admin_a_client):
        resp = admin_a_client.post("/api/v1/pos/devices/register/", {"device_name": "Till A", "device_role": "canteen"}, format="json")
        assert resp.status_code == 201 and len(resp.data["device_token"]) > 30
        token = resp.data["device_token"]
        listed = admin_a_client.get("/api/v1/pos/devices/").data["results"][0]
        assert "device_token" not in listed and listed["token_prefix"] == token[:8]
        device = Device.objects.get()
        assert device.token_hash != token
        assert device_client(token).get("/api/v1/pos/cache/").status_code == 200
        assert Device.objects.get().last_seen_at is not None

    def test_revoked_device_rejected_immediately(self, admin_a_client, canteen):
        device, client = canteen
        admin_a_client.post(f"/api/v1/pos/devices/{device.pk}/revoke/")
        assert client.get("/api/v1/pos/cache/").status_code == 401
        assert client.post("/api/v1/pos/sync/", {"transactions": []}, format="json").status_code == 401

    def test_rotate_token(self, admin_a_client, canteen):
        device, old_client = canteen
        new = admin_a_client.post(f"/api/v1/pos/devices/{device.pk}/rotate-token/").data["device_token"]
        assert old_client.get("/api/v1/pos/cache/").status_code == 401
        assert device_client(new).get("/api/v1/pos/cache/").status_code == 200

    def test_jwt_cannot_use_device_endpoints_and_devices_cannot_use_admin(self, admin_a_client, canteen):
        assert admin_a_client.get("/api/v1/pos/cache/").status_code in (401, 403)
        assert canteen[1].get("/api/v1/pos/devices/").status_code in (401, 403)
        assert APIClient().get("/api/v1/pos/cache/", HTTP_AUTHORIZATION="Device nonsense").status_code == 401

    def test_other_school_admin_cannot_manage(self, admin_b_client, canteen):
        device, _ = canteen
        assert admin_b_client.get("/api/v1/pos/devices/").data["results"] == []
        assert admin_b_client.post(f"/api/v1/pos/devices/{device.pk}/revoke/").status_code == 404

    def test_stale_devices(self, admin_a_client, canteen, canteen2):
        stale, _ = canteen
        Device.objects.filter(pk=stale.pk).update(created_at=timezone.now() - timedelta(days=3))
        Device.objects.filter(pk=canteen2[0].pk).update(last_sync_at=timezone.now())
        names = [d["device_name"] for d in admin_a_client.get("/api/v1/pos/devices/?stale=true").data["results"]]
        assert names == ["Canteen 1"]


@pytest.mark.django_db
class TestCache:
    def test_cache_contents_and_scope(self, canteen, funded_student_a1, student_b1, catalog):
        issue_card(student_b1, "9999")
        data = canteen[1].get("/api/v1/pos/cache/").data
        assert data["full"] is True and data["pin_hash_scheme"]["algorithm"] == "md5"  # tests use the fast hasher
        assert [c["student_id"] for c in data["cards"]] == [funded_student_a1.pk]  # school A only
        card = data["cards"][0]
        assert card["balance"] == "10000.00" and card["status"] == "active"
        assert card["pin_hash"] == funded_student_a1.cards.get().pin_hash and card["today_spend"] == "0.00"
        assert card["policy"]["p2p_enabled"] is True
        assert data["offline_spend_ceilings"] == {str(funded_student_a1.school_id): "2000.00"}
        assert {p["name"] for p in data["products"]} == {"Rice", "Soda"}

    def test_frozen_card_in_cache_and_incremental_refresh(self, canteen, funded_student_a1, school_a):
        other = Student.objects.create(school=school_a, name="Other Kid", class_name="P1")
        ensure_student_wallets(other)
        issue_card(other, "1111")
        first = canteen[1].get("/api/v1/pos/cache/").data
        assert len(first["cards"]) == 2
        since = first["generated_at"]
        freeze_card(funded_student_a1.cards.get())
        delta = canteen[1].get("/api/v1/pos/cache/", {"since": since}).data
        assert delta["full"] is False
        assert [(c["student_id"], c["status"]) for c in delta["cards"]] == [(funded_student_a1.pk, "frozen")]
        # a school-default policy change re-sends every card of the school
        policy = Policy.objects.get(school=school_a, student=None)
        policy.daily_spend_cap = Decimal("5000")
        policy.save()
        again = canteen[1].get("/api/v1/pos/cache/", {"since": delta["generated_at"]}).data
        assert len(again["cards"]) == 2 and again["cards"][0]["policy"]["daily_spend_cap"] == "5000.00"

    def test_other_school_device_sees_nothing_of_school_a(self, school_b, school_admin_b, funded_student_a1):
        _, raw = register_device(school_admin_b, school=school_b, device_name="B", device_role="canteen")
        assert device_client(raw).get("/api/v1/pos/cache/").data["cards"] == []


@pytest.mark.django_db
class TestSync:
    def test_apply_and_idempotent_replay(self, canteen, funded_student_a1, catalog, school_a):
        card = funded_student_a1.cards.get()
        batch = [sale(card, 3000, [line(catalog["rice"])]), sale(card, 1000, minutes_ago=4)]
        first = sync(canteen[1], *batch)
        assert [r["status"] for r in first["results"]] == ["applied", "applied"]
        assert first["balances"][0]["balance"] == "6000.00"
        assert first["balances"][0]["today_spend"] == "4000.00"
        replay = sync(canteen[1], *batch)
        assert [r["status"] for r in replay["results"]] == ["duplicate", "duplicate"]
        assert replay["balances"][0]["balance"] == "6000.00"
        assert PosTransaction.objects.count() == 2
        settlement = get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
        assert settlement.cached_balance == Decimal("4000")
        txn = PosTransaction.objects.get(amount=3000)
        assert txn.items.get().product == catalog["rice"]
        assert LedgerEntry.objects.filter(reference_id=f"pos:{txn.pk}").count() == 2
        assert canteen[0].__class__.objects.get(pk=canteen[0].pk).last_sync_at is not None
        assert_books_balanced(school_a)

    def test_offline_double_spend_becomes_shortfall_not_dropped(self, canteen, canteen2, funded_student_a1, school_a, school_admin_a):
        card = funded_student_a1.cards.get()  # balance 10,000
        sync(canteen[1], sale(card, 7000))
        second = sync(canteen2[1], sale(card, 7000))["results"][0]
        assert second["status"] == "shortfall"
        assert second["applied_amount"] == "3000.00" and second["shortfall_amount"] == "4000.00"
        assert "exceeds_offline_ceiling" in second["flags"]  # 4000 > default ceiling 2000
        wallet = get_student_wallet(funded_student_a1)
        assert wallet.cached_balance == 0
        txn = PosTransaction.objects.get(pk=second["transaction_id"])
        assert txn.review_status == "pending"
        assert NotificationEvent.objects.filter(user=school_admin_a, event_type="shortfall_flagged").exists()
        assert_books_balanced(school_a)

    def test_bad_transaction_never_fails_batch(self, canteen, funded_student_a1):
        card = funded_student_a1.cards.get()
        results = sync(
            canteen[1],
            sale(card, 500),
            {**sale(card, 100), "card_uid": "no-such-card"},
            {**sale(card, 100), "amount": "-5"},
            {**sale(card, 100), "items": [{"description": "x", "unit_price": "40", "quantity": 1}]},  # mismatch
            {"card_uid": card.card_uid, "amount": "100"},  # no key
            "garbage",
        )["results"]
        statuses = sorted((r["status"], r.get("reason")) for r in results)
        assert ("applied", None) in statuses
        reasons = {r.get("reason") for r in results if r["status"] == "rejected"}
        assert reasons == {"unknown_card", "amount_invalid", "amount_mismatch", "idempotency_key_required", "malformed"}

    def test_frozen_card_and_blocked_item_are_flagged(self, canteen, funded_student_a1, catalog, school_a):
        override = Policy.objects.create(school=school_a, student=funded_student_a1)
        override.blocked_items.add(catalog["soda"])
        card = funded_student_a1.cards.get()
        r1 = sync(canteen[1], sale(card, 1500, [line(catalog["soda"])]))["results"][0]
        assert r1["status"] == "applied" and r1["flags"] == ["item_blocked"]
        freeze_card(card)
        r2 = sync(canteen[1], sale(card, 1000))["results"][0]
        assert r2["status"] == "applied" and r2["flags"] == ["card_frozen"]
        assert PosTransaction.objects.filter(review_status="pending").count() == 2

    def test_pin_failures_lock_card(self, canteen, funded_student_a1, parent_user):
        card = funded_student_a1.cards.get()
        now = timezone.now().isoformat()
        sync(canteen[1], pin_failures=[{"card_uid": card.card_uid, "failed_attempts": 3, "device_local_timestamp": now}])
        card.refresh_from_db()
        assert card.status == "active"
        sync(canteen[1], pin_failures=[{"card_uid": card.card_uid, "failed_attempts": 2, "device_local_timestamp": now}])
        card.refresh_from_db()
        assert card.status == "frozen"
        assert NotificationEvent.objects.filter(user=parent_user, event_type="card_locked_pin_failures").exists()


@pytest.mark.django_db
class TestOnlinePurchase:
    def test_online_enforces_policy_in_real_time(self, canteen, funded_student_a1, school_a):
        policy = Policy.objects.get_or_create(school=school_a, student=None)[0]
        policy.per_transaction_cap = Decimal("2000")
        policy.save()
        card = funded_student_a1.cards.get()
        refused = canteen[1].post("/api/v1/pos/purchase/", {"idempotency_key": "o1", "card_uid": card.card_uid, "amount": "2500"}, format="json")
        assert refused.status_code == 422 and refused.data["code"] == "per_transaction_cap_exceeded"
        assert not PosTransaction.objects.exists()
        ok = canteen[1].post("/api/v1/pos/purchase/", {"idempotency_key": "o2", "card_uid": card.card_uid, "amount": "1500", "pin": "1234"}, format="json")
        assert ok.status_code == 201 and ok.data["status"] == "applied" and ok.data["balance"]["balance"] == "8500.00"
        again = canteen[1].post("/api/v1/pos/purchase/", {"idempotency_key": "o2", "card_uid": card.card_uid, "amount": "1500"}, format="json")
        assert again.status_code == 200 and again.data["status"] == "duplicate"

    def test_wrong_pin(self, canteen, funded_student_a1):
        card = funded_student_a1.cards.get()
        resp = canteen[1].post("/api/v1/pos/purchase/", {"idempotency_key": "p", "card_uid": card.card_uid, "amount": "100", "pin": "0000"}, format="json")
        assert resp.status_code == 422 and resp.data["code"] == "pin_invalid"
        assert PinFailureReport.objects.count() == 1

    def test_pos_p2p(self, canteen, funded_student_a1, school_a):
        friend = Student.objects.create(school=school_a, name="Friend Kid", class_name="P4")
        ensure_student_wallets(friend)
        fcard = issue_card(friend, "4321")
        card = funded_student_a1.cards.get()
        body = {"idempotency_key": "pp1", "sender_card_uid": card.card_uid, "pin": "1234",
                "recipient_card_uid": fcard.card_uid, "amount": "700"}
        assert canteen[1].post("/api/v1/pos/p2p-transfer/", body, format="json").status_code == 201
        assert canteen[1].post("/api/v1/pos/p2p-transfer/", body, format="json").status_code == 201  # replay
        assert get_student_wallet(friend).cached_balance == Decimal("700")
        bad = canteen[1].post("/api/v1/pos/p2p-transfer/", {**body, "idempotency_key": "pp2", "pin": "9999"}, format="json")
        assert bad.status_code == 422 and bad.data["code"] == "pin_invalid"


@pytest.mark.django_db
class TestShortfallReview:
    def make_shortfall(self, canteen, student):
        card = student.cards.get()
        return sync(canteen[1], sale(card, 12000))["results"][0]  # 10,000 balance -> 2,000 short

    def test_write_off(self, admin_a_client, canteen, funded_student_a1, school_a):
        r = self.make_shortfall(canteen, funded_student_a1)
        queue = admin_a_client.get("/api/v1/pos/shortfalls/").data["results"]
        assert [q["id"] for q in queue] == [r["transaction_id"]] and queue[0]["outstanding_amount"] == "2000.00"
        resp = admin_a_client.post(f"/api/v1/pos/shortfalls/{r['transaction_id']}/resolve/", {"resolution": "write_off"}, format="json")
        assert resp.status_code == 200 and resp.data["review_status"] == "resolved" and resp.data["outstanding_amount"] == "0.00"
        assert admin_a_client.get("/api/v1/pos/shortfalls/").data["results"] == []
        assert_books_balanced(school_a)

    def test_recover_from_next_topup(self, admin_a_client, canteen, funded_student_a1, school_a):
        r = self.make_shortfall(canteen, funded_student_a1)
        admin_a_client.post(f"/api/v1/pos/shortfalls/{r['transaction_id']}/resolve/", {"resolution": "recover_from_next_topup"}, format="json")
        txn = PosTransaction.objects.get(pk=r["transaction_id"])
        assert txn.review_status == "recovery_pending"
        wallet = get_student_wallet(funded_student_a1)
        fund_wallet(wallet, "500")  # not a confirmed deposit: no recovery yet
        dep = Deposit.objects.create(school=school_a, wallet=wallet, amount=Decimal("5000"), channel="momo",
                                     reference="SD-DEP-TEST1", idempotency_key="t1")
        mock_confirm(dep)
        txn.refresh_from_db()
        assert txn.review_status == "resolved" and txn.recovered_amount == Decimal("2000")
        wallet.refresh_from_db()
        assert wallet.cached_balance == Decimal("3500")
        assert LedgerEntry.objects.filter(entry_type="shortfall_recovery", direction="debit").count() == 1
        assert_books_balanced(school_a)

    def test_charge_guardian(self, admin_a_client, canteen, funded_student_a1, school_a):
        r = self.make_shortfall(canteen, funded_student_a1)
        admin_a_client.post(f"/api/v1/pos/shortfalls/{r['transaction_id']}/resolve/", {"resolution": "charge_guardian"}, format="json")
        dep = Deposit.objects.get(idempotency_key=f"shortfall:{r['transaction_id']}")
        assert dep.amount == Decimal("2000") and dep.initiated_by is not None
        mock_confirm(dep)
        txn = PosTransaction.objects.get(pk=r["transaction_id"])
        assert txn.review_status == "resolved"
        assert get_student_wallet(funded_student_a1).cached_balance == 0
        assert_books_balanced(school_a)

    def test_review_is_tenant_scoped(self, admin_b_client, canteen, funded_student_a1):
        r = self.make_shortfall(canteen, funded_student_a1)
        assert admin_b_client.get("/api/v1/pos/shortfalls/").data["results"] == []
        resp = admin_b_client.post(f"/api/v1/pos/shortfalls/{r['transaction_id']}/resolve/", {"resolution": "write_off"}, format="json")
        assert resp.status_code == 404

    def test_offline_ceiling_setting(self, admin_a_client, school_a):
        resp = admin_a_client.patch("/api/v1/school-settings/", {"offline_spend_ceiling": "5000"}, format="json")
        assert resp.status_code == 200 and get_school_settings(school_a).offline_spend_ceiling == Decimal("5000")

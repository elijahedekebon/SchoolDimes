"""Section I: public contributor page /give/<token>."""
import time
from decimal import Decimal

import pytest
from django.core import signing
from django.core.management import call_command

from notifications.models import NotificationEvent
from payments.services import create_topup_link, revoke_topup_link
from wallets.models import Wallet

from .conftest import hx, web_client

pytestmark = pytest.mark.django_db


@pytest.fixture
def link(funded_student_a1, parent_user):
    return create_topup_link(parent_user, funded_student_a1)


def shown(seconds_ago=10):
    return signing.dumps(time.time() - seconds_ago, salt="give-form-shown-at")


def form(page_html):
    return page_html.split('name="idempotency_key" value="')[1].split('"')[0]


def test_page_shows_only_first_name_and_school(link, funded_student_a1):
    body = web_client().get(f"/give/{link.token}").content.decode()
    first, *rest = funded_student_a1.name.split()
    assert f"Send money to {first}" in body and funded_student_a1.school.name in body
    for secret in rest + ["10,000", "10000", "balance"]:  # no surname, no balance or history
        assert secret not in body


def test_invalid_and_revoked_links_look_the_same(link):
    r = web_client().get("/give/not-a-real-token")
    assert r.status_code == 404 and 'data-testid="link-invalid"' in r.content.decode()
    revoke_topup_link(link)
    body = web_client().get(f"/give/{link.token}").content.decode()
    assert "This link isn" in body


def test_throttled(settings, link):
    settings.PUBLIC_TOPUP_THROTTLE_RATE = "2/min"
    c = web_client()
    c.get(f"/give/{link.token}")
    c.get(f"/give/{link.token}")
    r = c.get(f"/give/{link.token}")
    assert r.status_code == 429 and "Too many tries" in r.content.decode()


def test_bot_deterrent_and_csrf(link):
    c = web_client()
    key = form(c.get(f"/give/{link.token}").content.decode())
    data = {"name": "Jjajja", "phone_number": "0701000222", "amount": "1500", "channel": "momo",
            "idempotency_key": key}
    too_fast = c.post(f"/give/{link.token}", {**data, "shown": shown(0)}, **hx()).content.decode()
    assert "press Continue again" in too_fast
    honeypot = c.post(f"/give/{link.token}", {**data, "shown": shown(), "website": "spam"}, **hx()).content.decode()
    assert "press Continue again" in honeypot
    strict = web_client(csrf=True)
    assert strict.post(f"/give/{link.token}", {**data, "shown": shown()}).status_code == 403


def test_end_to_end_mock_payment(link, funded_student_a1, parent_user):
    main = Wallet.objects.get(student=funded_student_a1, wallet_type="main")
    before = main.cached_balance
    unread_before = NotificationEvent.objects.filter(user=parent_user, read_at__isnull=True).count()
    c = web_client()
    key = form(c.get(f"/give/{link.token}").content.decode())
    data = {"name": "Jjajja E2E", "phone_number": "0701000222", "amount": "1500", "channel": "momo",
            "idempotency_key": key, "shown": shown()}
    body = c.post(f"/give/{link.token}", data, **hx()).content.decode()
    assert "Waiting" in body and "load delay:3s" in body
    reference = body.split('data-testid="give-reference">')[1].split("<")[0]
    # a retry with the same key can never create a second collection
    again = c.post(f"/give/{link.token}", data, **hx()).content.decode()
    assert reference in again
    call_command("mock_webhook", reference)
    status = c.get(f"/give/{link.token}/status/{reference}?n=1", **hx()).content.decode()
    assert "Paid" in status and "Thank you!" in status and "load delay:3s" not in status
    main.refresh_from_db()
    assert main.cached_balance == before + Decimal("1500")
    assert NotificationEvent.objects.filter(user=parent_user, read_at__isnull=True).count() > unread_before


def test_gift_voucher_with_message(link, funded_student_a1):
    from payments.models import GiftVoucher

    c = web_client()
    key = form(c.get(f"/give/{link.token}").content.decode())
    c.post(f"/give/{link.token}", {"kind": "gift", "name": "Auntie", "email": "a@x.test", "amount": "2000",
                                   "channel": "bank", "message": "Happy birthday", "idempotency_key": key,
                                   "shown": shown()}, **hx())
    assert GiftVoucher.objects.get(student=funded_student_a1).message == "Happy birthday"


def test_validation_messages(link):
    c = web_client()
    key = form(c.get(f"/give/{link.token}").content.decode())
    body = c.post(f"/give/{link.token}", {"amount": "-1", "channel": "momo", "idempotency_key": key,
                                          "shown": shown()}, **hx()).content.decode()
    assert "Enter a positive amount, e.g. 5000" in body and "A phone number or an email" in body
    assert form(body) == key  # the same attempt keeps its key


def test_status_of_another_links_deposit_is_not_shown(link, funded_student_a1, other_parent, student_a2):
    from students.models import Guardian
    from wallets.services import ensure_student_wallets

    Guardian.objects.create(parent=other_parent, student=student_a2)
    ensure_student_wallets(student_a2)
    other = create_topup_link(other_parent, student_a2)
    c = web_client()
    key = form(c.get(f"/give/{other.token}").content.decode())
    body = c.post(f"/give/{other.token}", {"name": "X", "phone_number": "0700", "amount": "100", "channel": "momo",
                                           "idempotency_key": key, "shown": shown()}, **hx()).content.decode()
    reference = body.split('data-testid="give-reference">')[1].split("<")[0]
    assert "isn" in c.get(f"/give/{link.token}/status/{reference}", **hx()).content.decode()

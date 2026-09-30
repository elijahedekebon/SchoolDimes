"""
manage.py simulate_pos [--base-url http://localhost:8000]

Plays the part of the Android POS / merchant / attendance apps (Part 3)
against the seed data, over the REAL HTTP API with device-token auth:
  1. registers (or reuses, rotating tokens) a canteen, a second canteen, a
     merchant and an attendance device via the same service the
     /pos/devices/register/ endpoint uses;
  2. GET /api/v1/pos/cache/ as each device;
  3. builds offline batches: normal sales with line items, a double-spend of
     one card across two devices that exceeds its true balance, a sale on a
     card frozen after the cache was pulled, and a sale of a blocked item;
  4. POST /api/v1/pos/sync/ for each device, then replays one batch unchanged;
  5. POST /api/v1/attendance/tap/ with a batch including a duplicate;
  6. prints a summary.
Without --base-url it uses Django's test client (same URL routing, auth,
serializers and views; no server needed). With --base-url it makes real HTTP
calls with urllib to a running server (e.g. `docker compose up`).
"""
import json
import urllib.error
import urllib.request
import uuid
from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.test import Client
from django.utils import timezone

from accounts.models import User
from cards.services import freeze_card, unfreeze_card
from merchants.models import Merchant
from payments.services import initiate_collection, mock_confirm
from policies.models import Product
from pos.models import Device
from pos.services import register_device, rotate_device_token
from students.models import Student
from tenants.models import School
from wallets.services import get_student_wallet

SCHOOL = "Kampala Demo Primary School"
ADMIN = "admin@kampaladps.schooldimes.test"


class DjangoTransport:
    def __init__(self):
        self.client = Client()

    def request(self, method, path, token, body=None):
        kwargs = {"HTTP_AUTHORIZATION": f"Device {token}", "HTTP_X_APP_VERSION": "simulator-1.0"}
        if method == "GET":
            resp = self.client.get(path, **kwargs)
        else:
            resp = self.client.post(path, data=json.dumps(body), content_type="application/json", **kwargs)
        return resp.status_code, resp.json()


class HttpTransport:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip("/")

    def request(self, method, path, token, body=None):
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(self.base_url + path, data=data, method=method, headers={
            "Authorization": f"Device {token}", "Content-Type": "application/json", "X-App-Version": "simulator-1.0"})
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                return resp.status, json.loads(resp.read().decode())
        except urllib.error.HTTPError as exc:
            return exc.code, json.loads(exc.read().decode() or "{}")


def _device(admin, school, name, role, merchant=None):
    device = Device.objects.filter(school=school, device_name=name, status=Device.Status.ACTIVE).first()
    if device is None:
        return register_device(admin, school=school, device_name=name, device_role=role, merchant=merchant)
    return rotate_device_token(admin, device)


def _ensure_balance(student, minimum):
    """Tops up through the real deposit path (mock aggregator) so repeated
    simulator runs don't just drain everyone to zero."""
    wallet = get_student_wallet(student)
    if wallet.cached_balance < minimum:
        deposit, _ = initiate_collection(
            purpose="wallet_topup", wallet=wallet, amount=minimum - wallet.cached_balance + Decimal("5000"),
            channel="momo", payer_phone="0772000111", idempotency_key=f"simulator-topup-{uuid.uuid4()}")
        mock_confirm(deposit)


def run_simulation(transport, log=print) -> dict:
    school = School.objects.filter(name=SCHOOL).first()
    admin = User.objects.filter(email=ADMIN).first()
    merchant = Merchant.objects.filter(name="Ntinda Bookshop").first()
    if not (school and admin and merchant):
        raise CommandError("Seed data missing: run `python manage.py seed_demo` first.")
    students = {s.name.split()[0]: s for s in Student.objects.filter(school=school)}
    amina, brian, cynthia = students["Amina"], students["Brian"], students["Cynthia"]
    products = {p.name: p for p in Product.objects.filter(school=school)}
    for s in (amina, brian, cynthia):
        for frozen in s.cards.filter(status="frozen"):  # left over from an interrupted run
            unfreeze_card(frozen)
        _ensure_balance(s, Decimal("8000"))

    # 1. devices -----------------------------------------------------------
    devices = {
        "canteen_a": _device(admin, school, "Simulator canteen A", "canteen"),
        "canteen_b": _device(admin, school, "Simulator canteen B", "canteen"),
        "merchant": _device(admin, school, "Simulator bookshop", "merchant", merchant),
        "attendance": _device(admin, school, "Simulator gate", "attendance"),
    }
    token = {k: raw for k, (_d, raw) in devices.items()}
    log(f"Devices ready: {', '.join(f'{k} #{d.pk}' for k, (d, _r) in devices.items())}")

    # 2. pull caches -------------------------------------------------------
    caches = {}
    for name in ("canteen_a", "canteen_b", "merchant"):
        status, caches[name] = transport.request("GET", "/api/v1/pos/cache/", token[name])
        assert status == 200, (name, status, caches[name])
        log(f"GET /pos/cache/ as {name}: {len(caches[name]['cards'])} cards, {len(caches[name]['products'])} products")
    status, gate_cache = transport.request("GET", "/api/v1/pos/cache/", token["attendance"])
    log(f"GET /pos/cache/ as attendance: HTTP {status} (attendance devices can't sell)")
    cached = {c["student_id"]: c for c in caches["canteen_a"]["cards"]}
    card = {s: cached[s.pk]["card_uid"] for s in (amina, brian, cynthia)}

    now = timezone.now()

    def sale(student, lines, minutes_ago):
        items = [{"product_id": products[p].pk, "quantity": q, "unit_price": str(products[p].price)} for p, q in lines]
        amount = sum(Decimal(i["unit_price"]) * i["quantity"] for i in items)
        return {"idempotency_key": str(uuid.uuid4()), "card_uid": card[student], "amount": str(amount), "items": items,
                "device_local_timestamp": (now - timedelta(minutes=minutes_ago)).isoformat(), "pin_verified": True}

    # 3. offline batches ------------------------------------------------------
    cynthia_cached = Decimal(cached[cynthia.pk]["balance"])
    rice = products["Rice & beans"].price
    double_qty = max(1, int((cynthia_cached * Decimal("0.7")) // rice))  # each device alone is within the cached balance
    batch_a = [
        sale(amina, [("Rice & beans", 1)], 50),
        sale(amina, [("Soda", 1)], 45),                        # Soda is blocked for Amina
        sale(brian, [("Chapati", 2)], 40),                     # Brian's card gets frozen before sync
        sale(cynthia, [("Rice & beans", double_qty)], 35),     # double-spend, part 1
    ]
    batch_b = [sale(cynthia, [("Rice & beans", double_qty)], 30)]  # double-spend, part 2 (other till)
    batch_m = [sale(amina, [("Exercise book", 1), ("Pen", 1)], 20)]

    freeze_card(brian.cards.get(card_uid=card[brian]))
    log("Brian's card frozen by a parent AFTER the devices refreshed their caches.")

    # 4. sync + replay -------------------------------------------------------
    results = {}
    for name, batch in (("canteen_a", batch_a), ("canteen_b", batch_b), ("merchant", batch_m)):
        status, body = transport.request("POST", "/api/v1/pos/sync/", token[name], {"transactions": batch})
        assert status == 200, (name, status, body)
        results[name] = body
    status, replay = transport.request("POST", "/api/v1/pos/sync/", token["canteen_a"], {"transactions": batch_a})
    results["replay"] = replay

    # 5. attendance ---------------------------------------------------------------
    tap = lambda s, key, minutes, d="in": {"idempotency_key": key, "card_uid": card[s], "direction": d,  # noqa: E731
                                            "device_local_timestamp": (now - timedelta(minutes=minutes)).isoformat()}
    k1, k2, k3 = (str(uuid.uuid4()) for _ in range(3))
    status, attendance = transport.request("POST", "/api/v1/attendance/tap/", token["attendance"], {"taps": [
        tap(amina, k1, 180), tap(cynthia, k2, 175), tap(amina, k1, 180), tap(cynthia, k3, 5, "out")]})

    unfreeze_card(brian.cards.get(card_uid=card[brian]))  # leave the demo usable

    # 6. summary -------------------------------------------------------------------
    names = {card[s]: s.name for s in (amina, brian, cynthia)}
    all_results = [r for k in ("canteen_a", "canteen_b", "merchant") for r in results[k]["results"]]
    summary = {
        "applied": [r for r in all_results if r["status"] == "applied" and not r["flags"]],
        "shortfalls": [r for r in all_results if r["status"] == "shortfall"],
        "flagged": [r for r in all_results if r["flags"]],
        "rejected": [r for r in all_results if r["status"] == "rejected"],
        "replay_statuses": [r["status"] for r in replay["results"]],
        "attendance": attendance["results"],
        "attendance_created": attendance["created"],
    }
    balances = {}
    for k in ("canteen_a", "canteen_b", "merchant"):
        for b in results[k]["balances"]:
            balances[b["card_uid"]] = b

    log("")
    log("=" * 72)
    log("POS SIMULATION SUMMARY")
    log("=" * 72)
    for k, batch in (("canteen_a", batch_a), ("canteen_b", batch_b), ("merchant", batch_m)):
        log(f"\n{k}: POST /api/v1/pos/sync/ ({len(batch)} offline sales)")
        by_key = {t["idempotency_key"]: t for t in batch}
        for r in results[k]["results"]:
            t = by_key[r["idempotency_key"]]
            what = ", ".join(f"{i['quantity']}x {Product.objects.get(pk=i['product_id']).name}" for i in t["items"])
            extra = f" shortfall={r['shortfall_amount']}" if r["status"] == "shortfall" else ""
            extra += f" flags={r['flags']}" if r["flags"] else ""
            extra += f" reason={r['reason']}" if r.get("reason") else ""
            log(f"  {names[t['card_uid']]:<14} {what:<32} {r['amount']:>9} -> {r['status']}{extra}")
    log(f"\nReplay of canteen_a's batch unchanged: {summary['replay_statuses']}  "
        f"({'OK: no double effect' if set(summary['replay_statuses']) == {'duplicate'} else 'UNEXPECTED'})")
    log(f"\nAttendance: {summary['attendance_created']} records created; statuses "
        f"{[a['status'] for a in summary['attendance']]}")
    log("\nFinal authoritative balances (from the sync responses):")
    for uid, b in balances.items():
        log(f"  {names.get(uid, uid):<14} balance={b['balance']:>10}  today_spend={b['today_spend']:>9}  card={b['card_status']}")
    log(f"\nTotals: {len(summary['applied'])} applied cleanly, {len(summary['shortfalls'])} shortfall(s), "
        f"{len(summary['flagged'])} flagged for review, {len(summary['rejected'])} rejected, "
        f"{summary['replay_statuses'].count('duplicate')} duplicates ignored.")
    log("Review the shortfalls/flags: GET /api/v1/pos/shortfalls/ as the school admin.")
    return summary


class Command(BaseCommand):
    help = "Simulate POS/merchant/attendance devices against the API (no Android device needed)."

    def add_arguments(self, parser):
        parser.add_argument("--base-url", help="Use real HTTP against a running server, e.g. http://localhost:8000")

    def handle(self, *args, **options):
        transport = HttpTransport(options["base_url"]) if options.get("base_url") else DjangoTransport()
        run_simulation(transport, log=self.stdout.write)

"""
manage.py mock_webhook <reference> [--fail] [--reason declined] [--base-url URL]

Plays the payment aggregator in AGGREGATOR_MODE=mock: builds the signed
webhook for a pending deposit, gift voucher, pooled-fund contribution
(SD-DEP-/SD-GV-/SD-PF-...) or payout (SD-PO-...) and POSTs it to
/api/v1/payments/webhook/ -- through Django's test client by default, or
over real HTTP with --base-url. The signature, routing and idempotency are
exercised exactly as for a real callback.

    python manage.py mock_webhook --list           # show pending references
"""
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.test import Client

from payments.aggregator_client import MockAggregatorClient
from payments.models import Deposit, Payout


class Command(BaseCommand):
    help = "Confirm or fail a pending payment by sending a signed mock webhook."

    def add_arguments(self, parser):
        parser.add_argument("reference", nargs="?", help="SD-DEP-…, SD-GV-…, SD-PF-… or SD-PO-…")
        parser.add_argument("--fail", action="store_true", help="Send a failure instead of a success.")
        parser.add_argument("--reason", default="declined", help="failure_reason sent with --fail.")
        parser.add_argument("--list", action="store_true", help="List pending references and exit.")
        parser.add_argument("--base-url", help="POST to a running server instead of the test client.")

    def handle(self, *args, **opts):
        if settings.AGGREGATOR_MODE != "mock":
            raise CommandError("mock_webhook only works with AGGREGATOR_MODE=mock.")
        if opts["list"] or not opts["reference"]:
            pending = list(Deposit.objects.filter(status="pending").order_by("created_at"))
            self.stdout.write(f"{len(pending)} pending deposit(s):")
            for d in pending:
                self.stdout.write(f"  {d.reference:<28} {d.purpose:<26} {d.amount:>10}  wallet #{d.wallet_id}")
            for p in Payout.objects.filter(status="pending"):
                self.stdout.write(f"  {p.reference:<28} payout {p.purpose:<19} {p.amount:>10}")
            return

        ref = opts["reference"]
        obj = Deposit.objects.filter(reference=ref).first() or Payout.objects.filter(reference=ref).first()
        amount = obj.amount if obj else None
        raw, headers = MockAggregatorClient.build_webhook(
            reference=ref, aggregator_ref=getattr(obj, "aggregator_ref", "") or "",
            amount=amount, success=not opts["fail"], failure_reason=opts["reason"],
        )
        if obj is None:
            self.stdout.write(self.style.WARNING(f"No payment with reference {ref}; sending anyway (expect 'unmatched')."))

        if opts.get("base_url"):
            req = urllib.request.Request(opts["base_url"].rstrip("/") + "/api/v1/payments/webhook/", data=raw,
                                         method="POST", headers={"Content-Type": "application/json", **headers})
            try:
                with urllib.request.urlopen(req, timeout=30) as resp:
                    status, body = resp.status, json.loads(resp.read())
            except urllib.error.HTTPError as exc:
                status, body = exc.code, json.loads(exc.read() or b"{}")
        else:
            resp = Client().post("/api/v1/payments/webhook/", data=raw, content_type="application/json",
                                 HTTP_X_SCHOOLDIMES_SIGNATURE=headers["X-SchoolDimes-Signature"])
            status, body = resp.status_code, resp.json()

        self.stdout.write(f"POST /api/v1/payments/webhook/ -> HTTP {status} {body}")
        if obj is not None:
            obj.refresh_from_db()
            self.stdout.write(self.style.SUCCESS(f"{ref} is now: {obj.status}"
                                                 + (f" ({obj.failure_reason})" if obj.failure_reason else "")))
            wallet = getattr(obj, "wallet", None)
            if wallet is not None:
                wallet.refresh_from_db()
                self.stdout.write(f"Target wallet #{wallet.pk} balance: {wallet.cached_balance}")

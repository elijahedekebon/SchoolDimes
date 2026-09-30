"""
Payment aggregator abstraction (mobile money / bank / USSD collections and
payouts). Business code only ever talks to `get_aggregator_client()`.

AGGREGATOR_MODE=mock    -> MockAggregatorClient (default; no network calls)
AGGREGATOR_MODE=flutterwave | pesapal | dpo -> skeletons below, NOT implemented.

Webhook contract (what our /payments/webhook/ endpoint accepts after a
client's parse_webhook() normalises it) -- see API_CONTRACTS.md:
    {"reference": "SD-DEP-...", "aggregator_ref": "...", "status":
     "successful" | "failed", "amount": "5000.00", "failure_reason": ""}
"""
import hashlib
import hmac
import json
import secrets
from dataclasses import dataclass, field
from decimal import Decimal

from django.conf import settings


@dataclass
class CollectionResult:
    aggregator_ref: str
    status: str  # "pending" | "failed"
    instructions: dict = field(default_factory=dict)
    failure_reason: str = ""


@dataclass
class PayoutResult:
    aggregator_ref: str
    status: str  # "pending" | "successful" | "failed"
    failure_reason: str = ""


@dataclass
class WebhookEvent:
    reference: str
    aggregator_ref: str
    status: str  # "successful" | "failed"
    amount: Decimal | None
    failure_reason: str = ""
    raw: dict = field(default_factory=dict)


class AggregatorClient:
    """Interface every aggregator integration implements."""

    #: True when collections confirm themselves without a real customer
    #: approving a prompt (mock mode only). Recurring top-ups rely on it.
    auto_confirms = False

    def initiate_collection(self, *, reference, amount, channel, phone_number, description) -> CollectionResult:
        raise NotImplementedError

    def initiate_payout(self, *, reference, amount, phone_number, description) -> PayoutResult:
        raise NotImplementedError

    def verify_webhook_signature(self, raw_body: bytes, headers) -> bool:
        raise NotImplementedError

    def parse_webhook(self, raw_body: bytes) -> WebhookEvent:
        raise NotImplementedError

    def get_transaction_status(self, aggregator_ref: str) -> str:
        raise NotImplementedError


SIGNATURE_HEADER = "X-SchoolDimes-Signature"


def sign_body(raw_body: bytes, secret: str | None = None) -> str:
    secret = secret if secret is not None else settings.PAYMENT_AGGREGATOR_WEBHOOK_SECRET
    return hmac.new(secret.encode(), raw_body, hashlib.sha256).hexdigest()


class MockAggregatorClient(AggregatorClient):
    """
    Deterministic fake aggregator for development and tests.
    - Collections from a phone number ending in "999" fail at initiation.
    - Payouts to a phone number ending in "998" fail.
    - Webhooks are HMAC-SHA256(PAYMENT_AGGREGATOR_WEBHOOK_SECRET, raw body),
      hex, in the X-SchoolDimes-Signature header. `build_webhook()` produces
      one (used by `manage.py mock_webhook` and the tests).
    """

    auto_confirms = True

    def initiate_collection(self, *, reference, amount, channel, phone_number, description):
        aggregator_ref = f"MOCK-{secrets.token_hex(8).upper()}"
        if (phone_number or "").endswith("999"):
            return CollectionResult(aggregator_ref, "failed", {}, "declined")
        amount_txt = f"{Decimal(amount):,.0f}"
        if channel == "ussd":
            instructions = {
                "type": "ussd",
                "ussd_code": f"*165*88*{secrets.randbelow(900000) + 100000}#",
                "message": f"Dial the code and approve UGX {amount_txt}.",
            }
        elif channel == "bank":
            instructions = {
                "type": "bank_transfer",
                "bank_name": "Mock Bank Uganda",
                "account_name": "SchoolDimes Collections",
                "account_number": "9030000000001",
                "narration": reference,
                "message": f"Transfer UGX {amount_txt} using {reference} as the narration.",
            }
        else:
            instructions = {
                "type": "momo_prompt",
                "phone_number": phone_number,
                "message": f"Approve the payment of UGX {amount_txt} on your phone (MTN MoMo / Airtel Money).",
            }
        return CollectionResult(aggregator_ref, "pending", instructions)

    def initiate_payout(self, *, reference, amount, phone_number, description):
        aggregator_ref = f"MOCKPO-{secrets.token_hex(8).upper()}"
        if (phone_number or "").endswith("998"):
            return PayoutResult(aggregator_ref, "failed", "payout_failed")
        return PayoutResult(aggregator_ref, "successful")

    def verify_webhook_signature(self, raw_body, headers):
        given = headers.get(SIGNATURE_HEADER, "")
        return bool(given) and hmac.compare_digest(given, sign_body(raw_body))

    def parse_webhook(self, raw_body):
        data = json.loads(raw_body.decode() or "{}")
        amount = data.get("amount")
        return WebhookEvent(
            reference=str(data.get("reference", "")),
            aggregator_ref=str(data.get("aggregator_ref", "")),
            status=str(data.get("status", "")),
            amount=Decimal(str(amount)) if amount not in (None, "") else None,
            failure_reason=str(data.get("failure_reason", "")),
            raw=data,
        )

    def get_transaction_status(self, aggregator_ref):
        return "unknown"

    @staticmethod
    def build_webhook(*, reference, aggregator_ref="", amount=None, success=True, failure_reason="declined"):
        """Returns (raw_body_bytes, headers) exactly as the aggregator would send."""
        body = {
            "reference": reference,
            "aggregator_ref": aggregator_ref,
            "status": "successful" if success else "failed",
            "amount": str(amount) if amount is not None else None,
            "failure_reason": "" if success else failure_reason,
        }
        raw = json.dumps(body).encode()
        return raw, {SIGNATURE_HEADER: sign_body(raw)}


class _NotImplementedClient(AggregatorClient):
    """Skeleton for a real aggregator. Every method must be implemented
    against the provider's API before AGGREGATOR_MODE may select it."""

    name = "unimplemented"

    def _todo(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.name} integration is a skeleton only; see payments/aggregator_client.py"
        )

    initiate_collection = initiate_payout = verify_webhook_signature = _todo
    parse_webhook = get_transaction_status = _todo


class FlutterwaveClient(_NotImplementedClient):
    # TODO: POST {BASE_URL}/v3/charges?type=mobile_money_uganda for collections,
    # POST /v3/transfers for payouts, verify the `verif-hash` header against
    # PAYMENT_AGGREGATOR_WEBHOOK_SECRET, map `tx_ref` -> our reference.
    name = "flutterwave"


class PesapalClient(_NotImplementedClient):
    # TODO: OAuth token via /api/Auth/RequestToken, SubmitOrderRequest for
    # collections, IPN registration + GetTransactionStatus for confirmation.
    name = "pesapal"


class DPOClient(_NotImplementedClient):
    # TODO: createToken / chargeTokenMobile XML API; verifyToken on callback.
    name = "dpo"


_CLIENTS = {
    "mock": MockAggregatorClient,
    "flutterwave": FlutterwaveClient,
    "pesapal": PesapalClient,
    "dpo": DPOClient,
}


def get_aggregator_client() -> AggregatorClient:
    return _CLIENTS[settings.AGGREGATOR_MODE]()

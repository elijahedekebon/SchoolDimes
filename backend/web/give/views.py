"""Public contributor page /give/<token> (was src/app/give/[token]/page.tsx).

No login, no app. Shows ONLY the student's first name and the school's name.
Per-IP throttle (PUBLIC_TOPUP_THROTTLE_RATE) as on the public API -- served
by Django itself, so the throttle sees each contributor's real IP. Cheap bot
deterrent: a hidden honeypot field and a 3-second minimum fill time. One
idempotency key per attempt, kept on a retry, renewed only after success."""
import time
import uuid

from django.core import signing
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.views import View

from payments import services
from payments.serializers import PublicContributionSerializer, PublicDepositSerializer, PublicGiftVoucherSerializer
from payments.throttles import PublicTopUpThrottle
from web.core.errors import HANDLED, as_error
from web.core.money import format_ugx, is_valid_amount

MIN_FILL_SECONDS = 3
MAX_POLLS = 60  # every 3 s -> ~3 minutes
SIGNER_SALT = "give-form-shown-at"


class _GiveBase(View):
    def throttled(self, request):
        return not PublicTopUpThrottle().allow_request(request, self)

    def busy(self, request):
        return render(request, "give/detail.html", {"busy": True}, status=429)

    def link(self, token):
        return services.resolve_topup_link(token)


def form_context(token, info, data=None, *, key=None, error=None, field_errors=None, notice=None):
    data = data or {}
    amount = (data.get("amount") or "").strip()
    return {
        "token": token, "info": info, "data": data, "error": error, "field_errors": field_errors or {},
        "notice": notice, "kind": data.get("kind", "topup"), "channel": data.get("channel", "momo"),
        "key": key or str(uuid.uuid4()), "shown": signing.dumps(time.time(), salt=SIGNER_SALT),
        "amount_label": format_ugx(amount) if is_valid_amount(amount) else "",
    }


class GiveView(_GiveBase):
    def get(self, request, token):
        if self.throttled(request):
            return self.busy(request)
        link = self.link(token)
        if link is None:
            return render(request, "give/detail.html", {"invalid": True}, status=404)
        info = services.public_link_info(link)
        tpl = "give/_form.html" if request.headers.get("HX-Request") else "give/detail.html"
        return render(request, tpl, form_context(token, info))

    def post(self, request, token):
        if self.throttled(request):
            return render(request, "give/_busy.html", status=200)
        link = self.link(token)
        if link is None:
            return render(request, "give/_invalid.html")
        info = services.public_link_info(link)
        data = request.POST
        key = data.get("idempotency_key") or str(uuid.uuid4())
        # bot trap: humans never see or fill "website", and need a few seconds
        try:
            shown = signing.loads(data.get("shown", ""), salt=SIGNER_SALT, max_age=86400)
        except signing.BadSignature:
            shown = 0
        if data.get("website") or time.time() - float(shown) < MIN_FILL_SECONDS:
            return render(request, "give/_form.html", form_context(
                token, info, data, key=key, notice=_("Please check the details and press Continue again.")))
        errors = {}
        name, phone, email = (data.get(k, "").strip() for k in ("name", "phone_number", "email"))
        if not name:
            errors["name"] = _("Your name") + " *"
        if not phone and not email:
            errors["phone_number"] = _("A phone number or an email, so the family knows who sent it.")
        if not is_valid_amount(data.get("amount", "").strip()):
            errors["amount"] = _("Enter a positive amount, e.g. 5000")
        channel = data.get("channel", "momo")
        payer_phone = (data.get("payer_phone") or phone).strip()
        if channel != "bank" and not payer_phone:
            errors["payer_phone"] = _("Phone that will pay") + " *"
        if errors:
            return render(request, "give/_form.html", form_context(token, info, data, key=key, field_errors=errors))
        body = {
            "contributor": {"name": name, "phone_number": phone, "email": email,
                            "relationship_label": data.get("relationship_label", "").strip()},
            "amount": data["amount"].strip(), "channel": channel, "payer_phone": payer_phone, "idempotency_key": key,
        }
        try:
            if data.get("kind") == "gift":
                s = PublicGiftVoucherSerializer(data={**body, "message": data.get("message", "")})
                s.is_valid(raise_exception=True)
                voucher, _created = services.create_public_gift_voucher(link, s.validated_data)
                deposit = voucher.deposit
            else:
                s = PublicContributionSerializer(data=body)
                s.is_valid(raise_exception=True)
                d = s.validated_data
                deposit, _created = services.create_contributor_deposit(
                    link, contributor_data=d["contributor"], amount=d["amount"], channel=d["channel"],
                    payer_phone=d.get("payer_phone", ""), idempotency_key=d["idempotency_key"])
        except HANDLED as exc:
            return render(request, "give/_form.html", form_context(token, info, data, key=key, error=as_error(exc)))
        return render(request, "give/_status.html", status_context(token, info, deposit, 0))


def status_context(token, info, deposit, polls):
    d = PublicDepositSerializer(deposit).data
    return {"token": token, "info": info, "d": d, "polls": polls, "next_poll": polls + 1,
            "pending": d["status"] == "pending", "give_up": polls >= MAX_POLLS}


class GiveStatusView(_GiveBase):
    """Polled every 3 s by HTMX while the payment is pending."""

    def get(self, request, token, reference):
        if self.throttled(request):
            # keep polling through a throttle hiccup, like the React page did
            return render(request, "give/_poll_retry.html", {"url": request.get_full_path()})
        link = self.link(token)
        if link is None:
            return render(request, "give/_invalid.html")
        try:
            polls = min(int(request.GET.get("n", "0")), MAX_POLLS)
        except ValueError:
            polls = 0
        from django.http import Http404

        try:
            deposit = services.public_deposit_status(link, reference)
        except Http404:
            return render(request, "give/_invalid.html")
        return render(request, "give/_status.html", status_context(token, services.public_link_info(link), deposit, polls))

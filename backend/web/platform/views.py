"""Platform back-office pages (was src/app/platform/**). platform_admin only;
cross-tenant reads always name the school (?school=), writes are audit-logged
by the services."""
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from analytics import services as analytics
from backoffice import services as backoffice
from backoffice.serializers import AuditLogSerializer, OnboardSerializer, UnmatchedWebhookSerializer
from cards.serializers import CardSerializer
from pos.serializers import DeviceSerializer, PosTransactionSerializer
from students.serializers import StudentSerializer
from tenants.serializers import SchoolReferralSerializer
from tenants.services import apply_referral_reward
from web.core.actions import ConfirmView
from web.core.dates import kampala_today, shift_day
from web.core.mixins import ActionView, PageView
from web.core.paging import paginate
from web.core.shared import DepositIssuesMixin, TipDeleteView, TipFormView, TipsMixin
from web.school.views_setup import money_errors

LANGS = [("en", "English"), ("lg", "Luganda"), ("sw", "Kiswahili")]


def school_options(view):
    return [(s.pk, s.name) for s in view.scoped("schools").order_by("name")[:100]]


def school_param(view):
    value = view.params.get("school", "")
    return value if str(value).isdigit() else ""


class SchoolsView(PageView):
    template_name = "platform/index.html"
    regions = {"schools_table": ("platform/_schools.html", "table")}

    def table(self):
        return {"rows": backoffice.school_stats()}


class OnboardView(ActionView):
    """The onboarding wizard: one form, four steps, one atomic service call."""

    template_name = "platform/onboard/index.html"
    form_fields = ()

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name, self.page({}))

    def page(self, data, error=None, field_errors=None):
        posted = bool(data)
        return {
            "langs": LANGS, "data": data, "error": error, "field_errors": field_errors or {},
            "languages": data.getlist("supported_languages") if posted else ["en"],
            "values": {
                "primary_color": data.get("primary_color", "#0E7C66") if posted else "#0E7C66",
                "low_balance_threshold": data.get("low_balance_threshold", "2000") if posted else "2000",
                "offline_spend_ceiling": data.get("offline_spend_ceiling", "2000") if posted else "2000",
                "pin_lockout_threshold": data.get("pin_lockout_threshold", "5") if posted else "5",
                "p2p_enabled": bool(data.get("p2p_enabled")) if posted else True,
            },
            "caps": [("daily_spend_cap", _("Daily spend cap")), ("weekly_spend_cap", _("Weekly spend cap")),
                     ("per_transaction_cap", _("Per-transaction cap")), ("p2p_daily_cap", _("P2P daily cap")),
                     ("low_balance_threshold", _("Low-balance alert level"))],
            "start": 4 if posted else 0,
        }

    def post(self, request, *args, **kwargs):
        from web.core.errors import HANDLED, as_error

        data = request.POST
        caps = ["daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "low_balance_threshold"]
        errors = money_errors(data, caps)
        errors.update(money_errors(data, ["offline_spend_ceiling"], allow_empty=False))
        if errors:
            return render(request, self.template_name, self.page(data, field_errors=errors))
        body = {
            "name": data.get("name", "").strip(), "address": data.get("address", ""),
            "branding": {"logo_url": data.get("logo_url", ""), "primary_color": data.get("primary_color", "")},
            "supported_languages": data.getlist("supported_languages"),
            "policy": {**{c: (data.get(c) or None) for c in caps}, "p2p_enabled": bool(data.get("p2p_enabled"))},
            "settings": {"offline_spend_ceiling": data.get("offline_spend_ceiling"),
                         "pin_lockout_threshold": data.get("pin_lockout_threshold") or 5,
                         "attendance_notify_guardians": bool(data.get("attendance_notify_guardians")),
                         "attendance_on_canteen_devices": bool(data.get("attendance_on_canteen_devices"))},
            "admin": {k: data.get(k, "").strip() for k in ("full_name", "email", "phone_number")} | {
                "password": data.get("password", "")},
        }
        try:
            s = OnboardSerializer(data=body)
            s.is_valid(raise_exception=True)
            d = s.validated_data
            school, admin = backoffice.onboard_school(
                request.user, name=d["name"], address=d.get("address", ""), branding=d.get("branding"),
                supported_languages=d.get("supported_languages"), policy=d.get("policy"),
                settings=d.get("settings"), admin=d["admin"])
        except HANDLED as exc:
            return render(request, self.template_name, self.page(data, error=as_error(exc)))
        return render(request, "platform/onboard/done.html", {"school": school, "admin": admin})


class ReferralsView(PageView):
    template_name = "platform/referrals/index.html"
    regions = {"referrals_table": ("platform/referrals/_table.html", "table")}

    def table(self):
        names = dict(school_options(self))
        page = paginate(self.scoped("referrals").order_by("-created_at", "-pk"), self.params)
        rows = [{**r, "referring_name": names.get(r["referring_school"], f"#{r['referring_school']}"),
                 "referred_name": names.get(r["referred_school"], f"#{r['referred_school']}")}
                for r in SchoolReferralSerializer(page.object_list, many=True).data]
        return {"page": page, "rows": rows}


class NewReferralView(ActionView):
    template_name = "platform/referrals/_new.html"

    def dialog_context(self):
        return {"schools": school_options(self)}

    def validate(self, data):
        a, b = data.get("referring_school"), data.get("referred_school")
        if not a or not b or a == b:
            return {"referred_school": _("Referred school") + " *"}
        return {}

    def perform(self, data):
        s = SchoolReferralSerializer(data={"referring_school": data["referring_school"],
                                           "referred_school": data["referred_school"]})
        s.is_valid(raise_exception=True)
        return s.save()


class ApplyReferralView(ConfirmView):
    title = gettext_lazy("Apply referral reward")
    color = "green"

    def setup_object(self):
        self.referral = self.scoped_object("referrals", self.kwargs["pk"])

    def get_description(self):
        return _("Marks the referral applied and the reward for %(school)s as granted.") % {
            "school": self.referral.referring_school.name}

    def perform(self, data):
        return apply_referral_reward(self.referral)


class SupportView(PageView):
    """Read-only views of one school; every query names it (?school=)."""

    template_name = "platform/support/index.html"
    regions = {"support_body": ("platform/support/_body.html", "body"),
               "support_students": ("platform/support/_students.html", "students"),
               "support_cards": ("platform/support/_cards.html", "cards"),
               "support_devices": ("platform/support/_devices.html", "devices"),
               "support_transactions": ("platform/support/_transactions.html", "transactions")}
    page_regions = ("support_body",)

    def page_context(self):
        return {"school": school_param(self), "schools": school_options(self)}

    def body(self):
        school = school_param(self)
        if not school:
            return {}
        today = kampala_today()
        school_ids, _cross = analytics.school_scope(self.request.user, {"school": school})
        sales = analytics.sales_summary(school_ids, *analytics.date_range({"from": shift_day(today, -29), "to": today}))
        return {"sales": sales, **self.students(), **self.cards(), **self.devices(), **self.transactions()}

    def _page(self, name, serializer, key):
        qs = self.scoped(name, {"school": school_param(self)})
        qs = qs.order_by("-pk") if hasattr(qs, "order_by") else qs
        page = paginate(qs, self.params)
        return {f"{key}_page": page, f"{key}_rows": serializer(page.object_list, many=True).data}

    def students(self):
        return self._page("students", StudentSerializer, "students")

    def cards(self):
        return self._page("cards", CardSerializer, "cards")

    def devices(self):
        return self._page("devices", DeviceSerializer, "devices")

    def transactions(self):
        return self._page("transactions", PosTransactionSerializer, "txns")


class SupportTransactionView(PageView):
    def get(self, request, pk):
        txn = self.scoped_object("transactions", pk)
        return render(request, "school/sales/_transaction_drawer.html", {"t": PosTransactionSerializer(txn).data})


class PaymentIssuesView(DepositIssuesMixin, PageView):
    template_name = "platform/payment-issues/index.html"
    regions = {"webhooks_table": ("platform/payment-issues/_webhooks.html", "webhooks"),
               "deposit_issues": ("core/components/deposit_issues.html", "issues")}

    def page_context(self):
        return {"schools": school_options(self), "school": school_param(self)}

    def webhooks(self):
        reviewed = self.params.get("reviewed", "false") if "reviewed" in self.params else "false"
        page = paginate(self.scoped("webhooks", {"reviewed": reviewed}).order_by("-received_at", "-pk"), self.params)
        rows = []
        for h in UnmatchedWebhookSerializer(page.object_list, many=True).data:
            import json

            rows.append({**h, "payload_text": json.dumps(h["payload"])[:120]})
        return {"hooks_page": page, "hook_rows": rows, "reviewed": reviewed}

    def issues(self):
        return self.deposit_issues(school=school_param(self))


class MarkWebhookReviewedView(ConfirmView):
    title = gettext_lazy("Mark reviewed")
    description = gettext_lazy("Record that someone has looked into this webhook (e.g. reconciled with the "
                               "aggregator's dashboard). No money moves.")

    def setup_object(self):
        self.hook = self.scoped_object("webhooks", self.kwargs["pk"])

    def perform(self, data):
        return backoffice.mark_webhook_reviewed(self.request.user, self.hook)


class AuditLogView(PageView):
    template_name = "platform/audit-log/index.html"
    regions = {"audit_table": ("platform/audit-log/_table.html", "table")}

    def page_context(self):
        return {"schools": school_options(self), "school": school_param(self), "action": self.params.get("action", "")}

    def table(self):
        import json

        filters = {"school": school_param(self), "action": self.params.get("action", "").strip()}
        page = paginate(self.scoped("audit_logs", filters), self.params)
        rows = [{**r, "details_text": json.dumps(r["details"])}
                for r in AuditLogSerializer(page.object_list, many=True).data]
        return {"page": page, "rows": rows}


class TipsView(TipsMixin, PageView):
    template_name = "platform/tips/index.html"
    regions = {"tips_table": ("core/components/tips_table.html", "tips")}
    global_tips = True
    base_url = "/platform/tips"


class PlatformTipFormView(TipFormView):
    global_tips = True


class PlatformTipDeleteView(TipDeleteView):
    pass

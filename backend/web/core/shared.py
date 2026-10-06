"""Views shared by the school and platform areas (were components/TipsManager.tsx
and components/PaymentIssues.tsx)."""
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from content.serializers import FinancialLiteracyTipSerializer
from content.services import can_manage_tip, create_tip
from payments.serializers import DepositSerializer

from .actions import ConfirmView
from .mixins import ActionView
from .paging import paginate

LANGS = [("en", "English"), ("lg", "Luganda"), ("sw", "Kiswahili")]


class TipsMixin:
    """TipsManager. `global_tips` (platform) manages school=null tips only."""

    global_tips = False
    base_url = "/school/tips"

    def tips(self):
        language = self.params.get("language", "")
        page = paginate(self.scoped("tips", {"language": language}).order_by("-created_at", "-pk"), self.params)
        rows = [r for r in FinancialLiteracyTipSerializer(page.object_list, many=True).data
                if (r["school"] is None if self.global_tips else True)]
        for r in rows:
            r["language_label"] = dict(LANGS).get(r["language"], r["language"])
            r["editable"] = self.global_tips or r["school"] is not None
        return {"page": page, "rows": rows, "language": language, "langs": LANGS, "base_url": self.base_url}


class TipFormView(ActionView):
    template_name = "core/components/tip_form.html"
    global_tips = False
    form_fields = ("title", "body", "language", "target_age_range")

    def setup_object(self):
        self.obj = self.scoped_object("tips", self.kwargs["pk"]) if "pk" in self.kwargs else None
        if self.obj is not None and not can_manage_tip(self.request.user, self.obj):
            from django.http import Http404

            raise Http404

    def dialog_context(self):
        return {"obj": self.obj, "langs": LANGS}

    def validate(self, data):
        errors = {}
        if not data.get("title", "").strip():
            errors["title"] = _("Title") + " *"
        if not data.get("body", "").strip():
            errors["body"] = _("Tip") + " *"
        return errors

    def perform(self, data):
        body = {k: data.get(k, "").strip() for k in ("title", "body", "language", "target_age_range")}
        body["language"] = body["language"] or "en"
        if self.global_tips:
            body["school"] = None
        if self.obj:
            s = FinancialLiteracyTipSerializer(self.obj, data=body, partial=True)
            s.is_valid(raise_exception=True)
            return s.save()
        s = FinancialLiteracyTipSerializer(data=body)
        s.is_valid(raise_exception=True)
        return create_tip(self.request.user, s)


class TipDeleteView(ConfirmView):
    title = gettext_lazy("Delete")
    color = "red"

    def setup_object(self):
        self.obj = self.scoped_object("tips", self.kwargs["pk"])
        if not can_manage_tip(self.request.user, self.obj):
            from django.http import Http404

            raise Http404

    def get_description(self):
        return _('Delete "%(title)s"?') % {"title": self.obj.title}

    def perform(self, data):
        self.obj.delete()


class DepositIssuesMixin:
    """Failed / expired / long-pending collections (deposits, gift vouchers,
    fund contributions)."""

    def deposit_issues(self, school=None):
        status = self.params.get("status", "failed")
        filters = {"status": status, "school": school or ""}
        page = paginate(self.scoped("deposits", filters).order_by("-created_at", "-pk"), self.params)
        return {"page": page, "rows": DepositSerializer(page.object_list, many=True).data, "status": status,
                "status_options": [(v, v) for v in ("failed", "expired", "pending")]}

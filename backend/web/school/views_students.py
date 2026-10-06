"""Section D -- students (+ detail tabs), guardians & KYC, cards
(was src/app/school/{students,students/[id],guardians,cards} and
components/{StudentForm,cards}.tsx)."""
import re

from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.serializers import GuardianVerificationReviewSerializer, GuardianVerificationSerializer
from accounts.services import lookup_parent, review_guardian_verification
from attendance.services import student_attendance
from attendance.views import AttendanceRecordSerializer
from cards import services as card_services
from cards.serializers import CardSerializer, IssueCardSerializer, ReissueCardSerializer, ResetPinSerializer
from disputes.views import DisputeSerializer
from policies.serializers import PolicySerializer
from policies.services import get_effective_policy
from students import portal
from students.serializers import GuardianSerializer, StudentSerializer
from students.services import check_guardian_student, create_student, p2p_history
from wallets.serializers import LedgerEntrySerializer, P2PTransferSerializer, SavingsGoalSerializer, WalletSerializer
from web.core.actions import ConfirmView
from web.core.catalogue import catalogue, names
from web.core.errors import HANDLED, as_error
from web.core.htmx import hx_done, hx_redirect
from web.core.mixins import ActionView, PageView
from web.core.paging import paginate

PIN_RE = re.compile(r"^\d{4,6}$")
WALLET_LABELS = {"main": gettext_lazy("Main wallet"), "savings": gettext_lazy("Savings")}


def normalize_uid(raw):
    try:
        return card_services.normalize_card_uid(raw)
    except ValueError:
        return None


# ---------------------------------------------------------------------------
# /school/students
# ---------------------------------------------------------------------------

class StudentsView(PageView):
    template_name = "school/students/index.html"
    regions = {"students_table": ("school/students/_table.html", "table")}

    def page_context(self):
        return {"card_options": [("active", _("Active card")), ("frozen", _("Frozen card")),
                                 ("lost", _("Only lost cards")), ("none", _("No card"))]}

    def table(self):
        filters = {"search": self.params.get("search", "").strip(), "card_status": self.params.get("card_status", ""),
                   "low_balance": "true" if self.params.get("low_balance") else ""}
        page = paginate(self.scoped("students", filters).order_by("name", "pk"), self.params)
        return {"page": page, "rows": page.object_list, "filters": filters}


class StudentFormView(ActionView):
    """Create (POST /school/students/new) or edit (/school/students/<id>/edit)."""

    template_name = "school/students/_form.html"

    def setup_object(self):
        self.student = self.scoped_object("student", self.kwargs["pk"]) if "pk" in self.kwargs else None

    def render_dialog(self, extra=None):
        extra = dict(extra or {})
        data = extra.get("data")
        st = self.student
        if self.request.method == "POST":
            values = {k: data.get(k, "") for k in ("name", "class_name", "date_of_birth")}
        else:
            values = {"name": st.name if st else "", "class_name": st.class_name if st else "",
                      "date_of_birth": st.date_of_birth.isoformat() if st and st.date_of_birth else ""}
        extra["values"] = values
        return super().render_dialog(extra)

    def dialog_context(self):
        return {"student": self.student}

    def validate(self, data):
        errors = {}
        if not data.get("name", "").strip():
            errors["name"] = _("Name is required")
        if not data.get("class_name", "").strip():
            errors["class_name"] = _("Class is required")
        return errors

    def perform(self, data):
        body = {"name": data["name"].strip(), "class_name": data["class_name"].strip(),
                "date_of_birth": data.get("date_of_birth") or None}
        if self.student:
            s = StudentSerializer(self.student, data=body, partial=True)
            s.is_valid(raise_exception=True)
            return s.save()
        s = StudentSerializer(data=body)
        s.is_valid(raise_exception=True)
        return create_student(self.request.user, s)

    def success(self, result):
        if self.student:
            return hx_done(_("Done"))
        return hx_redirect(f"/school/students/{result.pk}")


# ---------------------------------------------------------------------------
# /school/students/<id> (tabs)
# ---------------------------------------------------------------------------

TABS = [("overview", gettext_lazy("Overview")), ("guardians", gettext_lazy("Guardians")),
        ("cards", gettext_lazy("Cards")), ("ledger", gettext_lazy("Ledger")), ("p2p", gettext_lazy("P2P")),
        ("attendance", gettext_lazy("Attendance")), ("disputes", gettext_lazy("Disputes")),
        ("portal", gettext_lazy("Student portal"))]


class StudentDetailView(PageView):
    template_name = "school/students/detail.html"
    regions = {"student_tab": ("school/students/_tab.html", "tab")}

    def page_context(self):
        self.student = self.scoped_object("student", self.kwargs["pk"])
        tab = self.params.get("tab", "overview")
        return {"student": self.student, "tabs": TABS, "tab": tab if tab in dict(TABS) else "overview"}

    def tab(self):
        tab = self.params.get("tab", "overview")
        tab = tab if tab in dict(TABS) else "overview"
        return {"tab": tab, **getattr(self, f"tab_{tab}")()}

    def tab_overview(self):
        s = self.student
        user = self.request.user
        cat = catalogue(user)
        p = get_effective_policy(s).to_dict()
        override = self.scoped("policies", {"student": s.pk}).first()
        lines = [
            (_("Daily cap"), p["daily_spend_cap"], True), (_("Weekly cap"), p["weekly_spend_cap"], True),
            (_("Per-transaction cap"), p["per_transaction_cap"], True),
            (_("P2P"), _("Allowed") if p["p2p_enabled"] else _("Off"), False),
            (_("P2P daily cap"), p["p2p_daily_cap"], True), (_("Low-balance alert"), p["low_balance_threshold"], True),
            (_("Blocked categories"), names(p["blocked_category_ids"], cat["categories"]), False),
            (_("Allowed categories"), names(p["allowed_category_ids"], cat["categories"])
             if p["allowed_category_ids"] is not None else _("All"), False),
            (_("Blocked items"), names(p["blocked_product_ids"], cat["products"]), False),
            (_("Blocked merchants"), names(p["blocked_merchant_ids"], cat["merchants"]), False),
        ]
        return {
            "wallets": [{**w, "label": WALLET_LABELS.get(w["wallet_type"], w["wallet_type"])}
                        for w in WalletSerializer(self.scoped("wallets", {"student": s.pk}), many=True).data],
            "goals": SavingsGoalSerializer(self.scoped("goals", {"student": s.pk}), many=True).data,
            "policy_lines": lines,
            "override": PolicySerializer(override).data if override else None,
        }

    def tab_guardians(self):
        return {"guardians": GuardianSerializer(self.scoped("guardians", {"student": self.student.pk}), many=True).data}

    def tab_cards(self):
        cards = CardSerializer(self.scoped("cards", {"student": self.student.pk}).order_by("-issued_at"), many=True).data
        return {"cards": cards, "has_usable": any(c["status"] != "lost" for c in cards)}

    def tab_ledger(self):
        wallets = list(self.scoped("wallets", {"student": self.student.pk}))
        chosen = self.params.get("wallet")
        wallet = next((w for w in wallets if str(w.pk) == chosen), None) or next(
            (w for w in wallets if w.wallet_type == "main"), None)
        page = paginate(wallet.ledger_entries.all(), self.params) if wallet else None
        return {"wallet_options": [(w.pk, WALLET_LABELS.get(w.wallet_type, w.wallet_type)) for w in wallets],
                "wallet": wallet, "page": page, "ledger_extra": f"&wallet={wallet.pk}" if wallet else "",
                "entries": LedgerEntrySerializer(page.object_list, many=True).data if page else []}

    def tab_p2p(self):
        page = paginate(p2p_history(self.student), self.params)
        return {"page": page, "rows": P2PTransferSerializer(page.object_list, many=True).data}

    def tab_attendance(self):
        page = paginate(student_attendance(self.student), self.params)
        return {"page": page, "rows": AttendanceRecordSerializer(page.object_list, many=True).data}

    def tab_disputes(self):
        page = paginate(self.scoped("disputes", {"student": self.student.pk}), self.params)
        return {"page": page, "rows": DisputeSerializer(page.object_list, many=True).data}

    def tab_portal(self):
        account = portal.portal_account_for(self.student)
        return {"account": account}


class GuardianLookupView(PageView):
    """The 'Find' button: exact-email parent lookup (GET /users/lookup/)."""

    def get(self, request, pk):
        student = self.scoped_object("student", pk)
        ctx = {"student": student, "email": request.GET.get("email", "")}
        try:
            ctx["found"] = lookup_parent(request.user, ctx["email"])
        except HANDLED as exc:
            ctx["lookup_error"] = as_error(exc)
        return render(request, "school/students/_lookup.html", ctx)


class LinkGuardianView(ConfirmView):
    title = gettext_lazy("Link guardian")
    confirm_label = gettext_lazy("Link")
    template_name = "school/students/_link.html"

    def setup_object(self):
        self.student = self.scoped_object("student", self.kwargs["pk"])
        params = self.request.POST if self.request.method == "POST" else self.request.GET
        self.parent = lookup_parent(self.request.user, params.get("email"))
        self.relationship = params.get("relationship") or "guardian"

    def get_description(self):
        return _("%(parent)s will be able to see %(student)s's balances and history, top up, set spending limits "
                 "and freeze the card.") % {"parent": self.parent.email, "student": self.student.name}

    def dialog_context(self):
        return {**super().dialog_context(), "parent": self.parent, "relationship": self.relationship}

    def perform(self, data):
        s = GuardianSerializer(data={"parent": self.parent.pk, "student": self.student.pk,
                                     "relationship": self.relationship})
        s.is_valid(raise_exception=True)
        check_guardian_student(self.request.user, s.validated_data["student"])
        return s.save()

    def get(self, request, *args, **kwargs):
        try:
            return super().get(request, *args, **kwargs)
        except HANDLED as exc:
            return render(request, "core/components/error_dialog.html", {"error": as_error(exc)})


class UnlinkGuardianView(ConfirmView):
    title = gettext_lazy("Unlink guardian")
    color = "red"

    def setup_object(self):
        self.link = self.scoped_object("guardians", self.kwargs["pk"])

    def get_description(self):
        return _("%(parent)s will no longer see or manage %(student)s's wallet, card or history. Their account is "
                 "not deleted.") % {"parent": self.link.parent.email, "student": self.link.student.name}

    def perform(self, data):
        self.link.delete()


class PortalCreateView(ActionView):
    template_name = "school/students/_portal_create.html"

    def setup_object(self):
        self.student = self.scoped_object("student", self.kwargs["pk"])

    def dialog_context(self):
        return {"student": self.student}

    def perform(self, data):
        return portal.create_portal_account(self.request.user, self.student, email=data.get("email"),
                                            password=data.get("password"))


class PortalRemoveView(ConfirmView):
    title = gettext_lazy("Remove portal login")
    description = gettext_lazy("The student will no longer be able to sign in to the portal. Their wallet and card "
                               "are unaffected.")
    color = "red"

    def setup_object(self):
        self.student = self.scoped_object("student", self.kwargs["pk"])

    def perform(self, data):
        portal.remove_portal_account(self.request.user, self.student)


# ---------------------------------------------------------------------------
# Cards (IssueCardButton, CardActions)
# ---------------------------------------------------------------------------

def _pin_errors(data):
    errors = {}
    pin, pin2 = data.get("pin", ""), data.get("pin2", "")
    if not PIN_RE.match(pin):
        errors["pin"] = _("4 to 6 digits. It is hashed at once and never shown again.")
    elif pin != pin2:
        errors["pin2"] = _("PINs don't match")
    return errors


class IssueCardView(ActionView):
    """Issue a first card (/school/cards/issue?student=) or replace one
    (/school/cards/<id>/reissue)."""

    template_name = "school/cards/_issue.html"
    success_message = gettext_lazy("Card issued")

    def setup_object(self):
        if "pk" in self.kwargs:
            self.replace = self.scoped_object("cards", self.kwargs["pk"])
            self.student = self.replace.student
        else:
            self.replace = None
            params = self.request.POST if self.request.method == "POST" else self.request.GET
            self.student = self.scoped_object("student", params.get("student"))

    def dialog_context(self):
        return {"student": self.student, "replace": self.replace}

    def validate(self, data):
        errors = _pin_errors(data)
        if data.get("card_uid", "").strip() and not normalize_uid(data["card_uid"]):
            errors["card_uid"] = _("Must be 4–32 bytes of hex, e.g. 04:A2:2B:7C")
        return errors

    def perform(self, data):
        body = {"pin": data["pin"]}
        if data.get("card_uid", "").strip():
            body["card_uid"] = data["card_uid"]
        if self.replace:
            s = ReissueCardSerializer(data=body)
            s.is_valid(raise_exception=True)
            return card_services.reissue_card(self.replace, s.validated_data["pin"],
                                              card_uid=s.validated_data.get("card_uid"))
        s = IssueCardSerializer(data={**body, "student": self.student.pk})
        s.is_valid(raise_exception=True)
        return card_services.issue_card(self.student, s.validated_data["pin"], card_uid=s.validated_data.get("card_uid"))


class CardUidPreviewView(PageView):
    """'Will be stored as …' under the UID field (validated by the server's own
    normalize_card_uid, so the preview is exactly what gets stored)."""

    def get(self, request):
        raw = request.GET.get("card_uid", "").strip()
        return render(request, "school/cards/_uid_preview.html", {"raw": raw, "normalized": normalize_uid(raw)})


class _CardConfirm(ConfirmView):
    def setup_object(self):
        self.card = self.scoped_object("cards", self.kwargs["pk"])

    def name(self):
        return self.card.student.name


class FreezeCardView(_CardConfirm):
    title = gettext_lazy("Freeze card")
    color = "cyan"

    def get_description(self):
        return _("Every purchase, transfer and fee payment from %(name)s's card is refused at once. Offline POS "
                 "devices refuse it after their next cache refresh. Guardians are notified.") % {"name": self.name()}

    def perform(self, data):
        return card_services.freeze_card_by(self.request.user, self.card)


class UnfreezeCardView(_CardConfirm):
    title = gettext_lazy("Unfreeze card")
    color = "green"

    def get_description(self):
        return _("%(name)s's card can be used again. Guardians are notified.") % {"name": self.name()}

    def perform(self, data):
        return card_services.unfreeze_card_by(self.request.user, self.card)


class MarkLostView(_CardConfirm):
    title = gettext_lazy("Mark card lost")
    color = "red"

    def get_description(self):
        return _("Permanent: %(name)s's card can never be used again. Issue a replacement afterwards.") % {
            "name": self.name()}

    def perform(self, data):
        return card_services.report_lost_by(self.request.user, self.card)


class ResetPinView(_CardConfirm):
    title = gettext_lazy("Set a new PIN")
    description = gettext_lazy("The old PIN stops working. POS devices pick up the new PIN on their next refresh. "
                               "A card frozen after wrong PINs stays frozen until you unfreeze it.")
    template_name = "school/cards/_reset_pin.html"

    def validate(self, data):
        return _pin_errors(data)

    def perform(self, data):
        if self.card.status == "lost":
            card_services.reset_pin_by(self.request.user, self.card, None)  # card_lost
        s = ResetPinSerializer(data={"pin": data["pin"]})
        s.is_valid(raise_exception=True)
        return card_services.reset_pin_by(self.request.user, self.card, s.validated_data["pin"])


class CardsView(PageView):
    template_name = "school/cards/index.html"
    regions = {"cards_table": ("school/cards/_table.html", "table")}

    def page_context(self):
        return {"status_options": [(v, v) for v in ("active", "frozen", "lost")]}

    def table(self):
        uid = self.params.get("card_uid", "").strip()
        filters = {"status": self.params.get("status", ""), "card_uid": (normalize_uid(uid) or uid) if uid else ""}
        page = paginate(self.scoped("cards", filters).order_by("-issued_at", "-pk"), self.params)
        return {"page": page, "rows": CardSerializer(page.object_list, many=True).data, "filters": filters}


# ---------------------------------------------------------------------------
# /school/guardians (KYC queue + all links)
# ---------------------------------------------------------------------------

class GuardiansView(PageView):
    template_name = "school/guardians/index.html"
    regions = {"kyc_table": ("school/guardians/_kyc.html", "kyc"),
               "links_table": ("school/guardians/_links.html", "links")}

    def page_context(self):
        return {"kyc_options": [(v, v) for v in ("pending", "verified", "rejected", "none")]}

    def kyc(self):
        page = paginate(self.scoped("verifications").order_by("-created_at", "-pk"), self.params)
        return {"kyc_page": page, "kyc_rows": GuardianVerificationSerializer(page.object_list, many=True).data}

    def links(self):
        page = paginate(self.scoped("guardians").order_by("student__name", "pk"), self.params)
        kyc = self.params.get("kyc", "")
        rows = [r for r in GuardianSerializer(page.object_list, many=True).data
                if not kyc or (r["verification_status"] or "none") == kyc]
        return {"links_page": page, "link_rows": rows, "kyc": kyc}


class ReviewKycView(ActionView):
    template_name = "school/guardians/_review.html"

    def setup_object(self):
        self.v = self.scoped_object("verifications", self.kwargs["pk"])

    def dialog_context(self):
        return {"v": self.v, "default": "rejected" if self.v.status == "verified" else "verified"}

    def perform(self, data):
        s = GuardianVerificationReviewSerializer(data={"status": data.get("status"),
                                                       "review_notes": data.get("review_notes", "")})
        s.is_valid(raise_exception=True)
        return review_guardian_verification(self.v, reviewer=self.request.user, status=s.validated_data["status"],
                                            notes=s.validated_data.get("review_notes", ""))

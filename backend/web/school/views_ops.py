"""Section F -- fees, attendance, pooled funds, disputes, P2P alerts, data
requests, tips, payment issues (was src/app/school/{fees,attendance,
pooled-funds,disputes,p2p-alerts,privacy,tips,payment-issues})."""
import uuid

from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from attendance.services import student_attendance
from attendance.views import AttendanceRecordSerializer
from disputes import services as dispute_services
from disputes.views import DisputeSerializer, ResolveSerializer
from fees import services as fee_services
from fees.views import FeeCategorySerializer, FeePaymentSerializer
from policies.services import create_catalog_item, update_catalog_item
from pooled_funds import services as fund_services
from pooled_funds.serializers import DisburseSerializer, PooledFundDetailSerializer, PooledFundSerializer
from privacy import services as privacy_services
from privacy.views import DataRequestSerializer
from students.services import p2p_history
from wallets import p2p as p2p_services
from wallets.serializers import P2PAlertSerializer, P2PTransferSerializer
from web.core.actions import ConfirmView
from web.core.csv import csv_response
from web.core.dates import kampala_today, time_only, valid_day
from web.core.mixins import ActionView, PageView
from web.core.money import compare_money, format_ugx, from_cents, is_valid_amount, to_cents
from web.core.paging import paginate
from web.core.shared import DepositIssuesMixin, TipDeleteView, TipFormView, TipsMixin
from .views import student_label
from .views_setup import money_errors


def new_key():
    """One idempotency key per attempt; renewed only after success."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# Fees
# ---------------------------------------------------------------------------

def amount_label(c):
    if c["amount_type"] == "fixed":
        return format_ugx(c["fixed_amount"])
    return f"{format_ugx(c['min_amount'])} – {format_ugx(c['max_amount'])}"


class FeesView(PageView):
    template_name = "school/fees/index.html"
    regions = {"fee_categories_table": ("school/fees/_categories.html", "categories"),
               "fee_payments_table": ("school/fees/_payments.html", "payments")}

    def page_context(self):
        cats = self.scoped("fee_categories")
        return {"category_options": [(c.pk, c.name) for c in list(cats)[:100]],
                "student_id": self.params.get("student", ""),
                "student_label": student_label(self, self.params.get("student"))}

    def categories(self):
        qs = self.scoped("fee_categories")
        qs = qs.order_by("name", "pk") if hasattr(qs, "order_by") else qs
        page = paginate(qs, self.params)
        rows = [{**c, "amount_label": amount_label(c)} for c in FeeCategorySerializer(page.object_list, many=True).data]
        return {"cat_page": page, "cat_rows": rows}

    def filters(self):
        return {"fee_category": self.params.get("fee_category", ""), "student": self.params.get("student", "")}

    def payments(self):
        f = self.filters()
        page = paginate(self.scoped("fee_payments", f).order_by("-created_at", "-pk"), self.params)
        return {"pay_page": page, "pay_rows": FeePaymentSerializer(page.object_list, many=True).data, "pay_filters": f}


class FeePaymentsExportView(FeesView):
    def get(self, request):
        self.params = request.GET
        rows = FeePaymentSerializer(self.scoped("fee_payments", self.filters()).order_by("-created_at", "-pk"),
                                    many=True).data
        return csv_response("fee-payments.csv", rows,
                            ["id", "created_at", "student_name", "fee_category_name", "amount", "status",
                             "ledger_reference"])


class FeeCategoryFormView(ActionView):
    template_name = "school/fees/_category_form.html"
    form_fields = ("name", "amount_type", "fixed_amount", "min_amount", "max_amount", "due_date",
                   "applicable_classes", "active")

    def setup_object(self):
        self.obj = self.scoped_object("fee_categories", self.kwargs["pk"]) if "pk" in self.kwargs else None

    def form_values(self, data):
        values = super().form_values(data)
        if self.request.method != "POST":
            values["applicable_classes"] = ", ".join(self.obj.applicable_classes) if self.obj else ""
            values["amount_type"] = values["amount_type"] or "fixed"
        return values

    def dialog_context(self):
        return {"obj": self.obj}

    def validate(self, data):
        errors = {} if data.get("name", "").strip() else {"name": _("Name") + " *"}
        kind = data.get("amount_type", "fixed")
        fields = ["fixed_amount"] if kind == "fixed" else ["min_amount", "max_amount"]
        errors.update(money_errors(data, fields, allow_empty=False))
        return errors

    def perform(self, data):
        kind = data.get("amount_type", "fixed")
        body = {
            "name": data["name"].strip(), "amount_type": kind,
            "fixed_amount": (data.get("fixed_amount") or None) if kind == "fixed" else None,
            "min_amount": (data.get("min_amount") or None) if kind == "range" else None,
            "max_amount": (data.get("max_amount") or None) if kind == "range" else None,
            "due_date": data.get("due_date") or None,
            "applicable_classes": [c.strip() for c in data.get("applicable_classes", "").split(",") if c.strip()],
            "active": bool(data.get("active")),
        }
        if self.obj:
            s = FeeCategorySerializer(self.obj, data=body, partial=True)
            s.is_valid(raise_exception=True)
            return update_catalog_item(self.request.user, s, "feecategory")
        s = FeeCategorySerializer(data=body)
        s.is_valid(raise_exception=True)
        return create_catalog_item(self.request.user, s, "feecategory")


class PayFeeView(ActionView):
    """PayFee: debits the student's main wallet now (idempotent)."""

    template_name = "school/fees/_pay.html"

    def setup_object(self):
        self.category = self.scoped_object("fee_categories", self.kwargs["pk"])

    def dialog_context(self):
        c = FeeCategorySerializer(self.category).data
        return {"category": c, "amount_label": amount_label(c),
                "key": (self.request.POST.get("idempotency_key") if self.request.method == "POST" else None) or new_key()}

    def validate(self, data):
        errors = {}
        if not data.get("student"):
            errors["student"] = _("Student") + " *"
        if self.category.amount_type == "range" and not is_valid_amount(data.get("amount", "")):
            errors["amount"] = "0.00"
        return errors

    def perform(self, data):
        student = self.scoped_object("student", data.get("student"))
        amount = data.get("amount") if self.category.amount_type == "range" else None
        return fee_services.pay_fee(self.request.user, student=student, fee_category=self.category, amount=amount,
                                    idempotency_key=data.get("idempotency_key"))


# ---------------------------------------------------------------------------
# Attendance
# ---------------------------------------------------------------------------

class AttendanceView(PageView):
    template_name = "school/attendance/index.html"
    regions = {"attendance_register": ("school/attendance/_register.html", "register"),
               "attendance_student": ("school/attendance/_student.html", "per_student")}

    def register_rows(self):
        day = valid_day(self.params.get("date"), kampala_today())
        class_name = self.params.get("class_name", "").strip()
        students = self.scoped("students", {"class_name": class_name}).order_by("name", "pk")
        records = list(self.scoped("attendance", {"date": day}).order_by("device_local_timestamp"))
        by_student = {}
        for r in records:
            by_student.setdefault(r.student_id, []).append(r)
        rows = []
        for s in students:
            recs = by_student.get(s.pk, [])
            ins = [r for r in recs if r.direction == "in"]
            outs = [r for r in recs if r.direction == "out"]
            rows.append({"id": s.pk, "name": s.name, "class_name": s.class_name,
                         "first_in": ins[0].device_local_timestamp if ins else None,
                         "last_out": outs[-1].device_local_timestamp if outs else None, "taps": len(recs)})
        return day, class_name, rows

    def register(self):
        day, class_name, rows = self.register_rows()
        return {"date": day, "class_name": class_name, "rows": rows,
                "present": sum(1 for r in rows if r["first_in"]), "total": len(rows)}

    def per_student(self):
        sid = self.params.get("student", "")
        if not sid:
            return {"student_id": "", "student_rows": None}
        student = self.scoped_object("student", sid)
        page = paginate(student_attendance(student), self.params)
        return {"student_id": sid, "student_label": student_label(self, sid), "student_page": page,
                "student_rows": AttendanceRecordSerializer(page.object_list, many=True).data}


class AttendanceRegisterExportView(AttendanceView):
    def get(self, request):
        self.params = request.GET
        day, class_name, rows = self.register_rows()
        out = [{"student": r["name"], "class": r["class_name"], "status": "present" if r["first_in"] else "absent",
                "first_in": time_only(r["first_in"]), "last_out": time_only(r["last_out"]), "taps": r["taps"]}
               for r in rows]
        return csv_response(f"attendance-{day}{'-' + class_name if class_name else ''}.csv", out,
                            ["student", "class", "status", "first_in", "last_out", "taps"])


class AttendanceStudentExportView(AttendanceView):
    def get(self, request):
        student = self.scoped_object("student", request.GET.get("student"))
        rows = AttendanceRecordSerializer(student_attendance(student), many=True).data
        return csv_response(f"attendance-student-{student.pk}.csv", rows,
                            ["device_local_timestamp", "direction", "device_name", "student_name"])


# ---------------------------------------------------------------------------
# Pooled funds
# ---------------------------------------------------------------------------

class PooledFundsView(PageView):
    template_name = "school/pooled-funds/index.html"
    regions = {"funds_table": ("school/pooled-funds/_table.html", "table")}

    def page_context(self):
        return {"status_options": [(v, v) for v in ("open", "closed", "disbursed")]}

    def table(self):
        status = self.params.get("status", "")
        page = paginate(self.scoped("funds", {"status": status}).order_by("-created_at", "-pk"), self.params)
        return {"page": page, "rows": PooledFundSerializer(page.object_list, many=True).data, "status": status}


class FundDrawerView(PageView):
    def get(self, request, pk):
        fund = self.scoped_object("funds_detail", pk)
        f = PooledFundDetailSerializer(fund).data
        return render(request, "school/pooled-funds/_drawer.html", {
            "f": f, "can_disburse": f["status"] != "disbursed" and compare_money(f["balance"], "0") > 0})


class NewFundView(ActionView):
    template_name = "school/pooled-funds/_new.html"
    form_fields = ("title", "purpose", "group_label", "target_amount", "deadline")

    def validate(self, data):
        errors = {} if data.get("title", "").strip() else {"title": _("Fund") + " *"}
        errors.update(money_errors(data, ["target_amount"]))
        return errors

    def perform(self, data):
        s = PooledFundSerializer(data={"title": data["title"].strip(), "purpose": data.get("purpose", ""),
                                       "group_label": data.get("group_label", ""),
                                       "target_amount": data.get("target_amount") or None,
                                       "deadline": data.get("deadline") or None})
        s.is_valid(raise_exception=True)
        d = s.validated_data
        return fund_services.create_fund(self.request.user, title=d["title"], purpose=d.get("purpose", ""),
                                         group_label=d.get("group_label", ""), target_amount=d.get("target_amount"),
                                         deadline=d.get("deadline"))


class CloseFundView(ConfirmView):
    title = gettext_lazy("Close this fund")
    description = gettext_lazy("No new contributions are accepted. Money already held stays in the fund until you "
                               "disburse it.")
    color = "orange"

    def setup_object(self):
        self.fund = self.scoped_object("funds", self.kwargs["pk"])

    def perform(self, data):
        return fund_services.close_fund(self.request.user, self.fund)


class DisburseView(ActionView):
    template_name = "school/pooled-funds/_disburse.html"

    def setup_object(self):
        self.fund = self.scoped_object("funds_detail", self.kwargs["pk"])
        self.balance = PooledFundSerializer(self.fund).data["balance"]

    def dialog_context(self):
        return {"fund": self.fund, "held": format_ugx(self.balance),
                "key": (self.request.POST.get("idempotency_key") if self.request.method == "POST" else None) or new_key()}

    def validate(self, data):
        errors = {}
        amount = data.get("amount", "").strip()
        if not is_valid_amount(amount):
            errors["amount"] = "0.00"
        elif compare_money(amount, self.balance) > 0:
            errors["amount"] = _("More than the fund holds")
        if not data.get("description", "").strip():
            errors["description"] = _("Required: what the money is for (shown in the transparent log).")
        if data.get("destination") == "external" and not data.get("phone_number", "").strip():
            errors["phone_number"] = _("Phone number") + " *"
        return errors

    def perform(self, data):
        s = DisburseSerializer(data={k: data.get(k, "") for k in ("amount", "destination", "description",
                                                                   "phone_number", "idempotency_key")})
        s.is_valid(raise_exception=True)
        return fund_services.disburse(self.request.user, self.fund, **s.validated_data)


# ---------------------------------------------------------------------------
# Disputes
# ---------------------------------------------------------------------------

class DisputesView(PageView):
    template_name = "school/disputes/index.html"
    regions = {"disputes_table": ("school/disputes/_table.html", "table")}

    def page_context(self):
        return {"status_options": [(v, v.replace("_", " ")) for v in ("open", "under_review", "resolved_refunded",
                                                                       "resolved_denied")],
                "open_id": self.params.get("open", "") if str(self.params.get("open", "")).isdigit() else ""}

    def table(self):
        status = self.params.get("status", "")
        page = paginate(self.scoped("disputes", {"status": status}).order_by("-created_at", "-pk"), self.params)
        return {"page": page, "rows": DisputeSerializer(page.object_list, many=True).data, "status": status}


class DisputeDrawerView(PageView):
    def get(self, request, pk):
        d = DisputeSerializer(self.scoped_object("disputes", pk)).data
        return render(request, "school/disputes/_drawer.html",
                      {"d": d, "is_open": d["status"] in ("open", "under_review")})


class StartReviewView(ConfirmView):
    title = gettext_lazy("Start review")
    description = gettext_lazy("Marks the dispute as under review; the parent is notified.")

    def setup_object(self):
        self.dispute = self.scoped_object("disputes", self.kwargs["pk"])

    def perform(self, data):
        return dispute_services.start_review(self.request.user, self.dispute)


class ResolveDisputeView(ActionView):
    """Refund (never above original − already refunded) or deny."""

    template_name = "school/disputes/_resolve.html"

    def setup_object(self):
        self.dispute = self.scoped_object("disputes", self.kwargs["pk"])
        d = DisputeSerializer(self.dispute).data
        self.d = d
        self.remaining = from_cents((to_cents(d["original_amount"]) or 0) - (to_cents(d["refunded_total"]) or 0))

    def dialog_context(self):
        return {"d": self.d, "remaining": self.remaining, "max": format_ugx(self.remaining)}

    def validate(self, data):
        if data.get("outcome", "refund") != "refund":
            return {}
        amount = data.get("refund_amount", "").strip()
        if not is_valid_amount(amount):
            return {"refund_amount": "0.00"}
        if compare_money(amount, self.remaining) > 0:
            return {"refund_amount": _("More than can be refunded")}
        return {}

    def perform(self, data):
        outcome = data.get("outcome", "refund")
        body = {"outcome": outcome, "resolution_notes": data.get("resolution_notes", "")}
        if outcome == "refund":
            body["refund_amount"] = data.get("refund_amount")
        s = ResolveSerializer(data=body)
        s.is_valid(raise_exception=True)
        return dispute_services.resolve(self.request.user, self.dispute, **s.validated_data)


# ---------------------------------------------------------------------------
# P2P alerts
# ---------------------------------------------------------------------------

RULE_LABELS = {"many_distinct_senders": gettext_lazy("Received from many different students"),
               "repeated_near_cap": gettext_lazy("Repeatedly sending close to the daily cap")}


class P2PAlertsView(PageView):
    template_name = "school/p2p-alerts/index.html"
    regions = {"alerts_table": ("school/p2p-alerts/_table.html", "table")}

    def page_context(self):
        return {"status_options": [(v, v) for v in ("open", "reviewed", "dismissed")]}

    def table(self):
        status = self.params.get("status", "open") if "status" in self.params else "open"
        page = paginate(self.scoped("p2p_alerts", {"status": status}).order_by("-created_at", "-pk"), self.params)
        rows = []
        for a in P2PAlertSerializer(page.object_list, many=True).data:
            details = " · ".join(f"{k.replace('_', ' ')}: {v}" for k, v in (a["details"] or {}).items())
            rows.append({**a, "rule_label": RULE_LABELS.get(a["rule"], a["rule"]), "details_text": details})
        return {"page": page, "rows": rows, "status": status}


class P2PHistoryDrawerView(PageView):
    def get(self, request, pk):
        alert = self.scoped_object("p2p_alerts", pk)
        page = paginate(p2p_history(alert.student), request.GET)
        return render(request, "school/p2p-alerts/_history.html", {
            "alert": alert, "page": page, "rows": P2PTransferSerializer(page.object_list, many=True).data})


class ReviewAlertView(ActionView):
    template_name = "school/p2p-alerts/_review.html"

    def setup_object(self):
        self.alert = self.scoped_object("p2p_alerts", self.kwargs["pk"])

    def dialog_context(self):
        return {"alert": self.alert}

    def perform(self, data):
        return p2p_services.review_alert(self.request.user, self.alert, data.get("status"),
                                         data.get("review_notes", ""))


# ---------------------------------------------------------------------------
# Data requests (privacy)
# ---------------------------------------------------------------------------

TYPE_LABELS = {"export": gettext_lazy("Export"), "correction": gettext_lazy("Correction"),
               "deletion": gettext_lazy("Deletion")}
HANDLE_HELP = {
    "export": gettext_lazy("The parent downloads their data in the app (My data). Mark completed once you've "
                           "confirmed it."),
    "correction": gettext_lazy("Make the correction on the student or account page first, then mark completed."),
    "deletion": gettext_lazy("Completing a deletion is irreversible. A student with money in their wallets can't be "
                             "redacted until it's withdrawn or spent."),
}


class PrivacyView(PageView):
    template_name = "school/privacy/index.html"
    regions = {"requests_table": ("school/privacy/_table.html", "table")}

    def page_context(self):
        return {"status_options": [(v, v.replace("_", " ")) for v in ("pending", "in_progress", "completed",
                                                                       "rejected")],
                "type_options": list(TYPE_LABELS.items())}

    def table(self):
        filters = {"status": self.params.get("status", "pending") if "status" in self.params else "pending",
                   "request_type": self.params.get("request_type", "")}
        page = paginate(self.scoped("data_requests", filters).order_by("-created_at", "-pk"), self.params)
        rows = [{**r, "type_label": TYPE_LABELS.get(r["request_type"], r["request_type"])}
                for r in DataRequestSerializer(page.object_list, many=True).data]
        return {"page": page, "rows": rows, "filters": filters}


class HandleRequestView(ActionView):
    template_name = "school/privacy/_handle.html"

    def setup_object(self):
        self.req = self.scoped_object("data_requests", self.kwargs["pk"])

    def dialog_context(self):
        r = DataRequestSerializer(self.req).data
        return {"r": r, "type_label": TYPE_LABELS.get(r["request_type"]), "help": HANDLE_HELP.get(r["request_type"]),
                "default": "in_progress" if r["status"] == "pending" else "completed",
                "statuses": [(v, v.replace("_", " ")) for v in ("in_progress", "completed", "rejected")]}

    def perform(self, data):
        return privacy_services.handle_request_by(self.request.user, self.req, status=data.get("status"),
                                                  notes=data.get("notes", ""))


# ---------------------------------------------------------------------------
# Tips & payment issues
# ---------------------------------------------------------------------------

class TipsView(TipsMixin, PageView):
    template_name = "school/tips/index.html"
    regions = {"tips_table": ("core/components/tips_table.html", "tips")}


class SchoolTipFormView(TipFormView):
    pass


class SchoolTipDeleteView(TipDeleteView):
    pass


class PaymentIssuesView(DepositIssuesMixin, PageView):
    template_name = "school/payment-issues/index.html"
    regions = {"deposit_issues": ("core/components/deposit_issues.html", "issues")}

    def issues(self):
        return self.deposit_issues()


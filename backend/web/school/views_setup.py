"""Section E -- devices (token once + QR), merchants, products, policy &
settings, staff accounts (was src/app/school/{devices,merchants,products,
policy,staff} and components/{DeviceToken,MoneyInput}.tsx)."""
from django.shortcuts import render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.serializers import SetPasswordSerializer, StaffUserSerializer
from accounts.services import create_staff_from, set_staff_password, update_staff_user
from merchants import services as merchant_services
from merchants.views import MerchantSerializer
from policies.serializers import PolicySerializer, ProductCategorySerializer, ProductSerializer
from policies.services import create_catalog_item, delete_catalog_item, update_catalog_item, update_policy
from pos import services as pos_services
from pos.serializers import DeviceRegisterSerializer, DeviceSerializer
from tenants.serializers import SchoolSettingsSerializer
from tenants.services import school_settings_for, update_school_settings
from wallets.serializers import LedgerEntrySerializer
from web.core.actions import ConfirmView
from web.core.catalogue import catalogue
from web.core.dates import hours_since, kampala_today, shift_day, valid_day
from web.core.errors import HANDLED, as_error
from web.core.htmx import hx_done
from web.core.mixins import ActionView, PageView
from web.core.money import is_valid_amount, to_cents
from web.core.paging import paginate
from web.core.qr import default_device_api_base, provisioning_payload, qr_svg

ROLE_LABELS = {"canteen": gettext_lazy("Canteen till"), "merchant": gettext_lazy("Merchant till"),
               "attendance": gettext_lazy("Attendance reader")}
ROLE_HELP = {
    "canteen": gettext_lazy("Sells canteen products; can also take attendance taps if enabled in Policy & settings."),
    "merchant": gettext_lazy("Belongs to an approved nearby merchant; sells only that merchant's products."),
    "attendance": gettext_lazy("Gate reader: records tap-in/out, never moves money."),
}


def approved_merchants(view):
    rows = MerchantSerializer(view.scoped("merchants")[:100], many=True, context={"request": view.request}).data
    return [m for m in rows if m["my_school_approval"] == "approved"]


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

class DevicesView(PageView):
    template_name = "school/devices/index.html"
    regions = {"devices_table": ("school/devices/_table.html", "table")}

    def stale_after(self):
        return school_settings_for(self.request.user, {}).device_stale_after_hours

    def page_context(self):
        return {"stale_after": self.stale_after(),
                "role_options": list(ROLE_LABELS.items()),
                "status_options": [("active", "active"), ("revoked", "revoked")]}

    def table(self):
        filters = {"device_role": self.params.get("device_role", ""), "status": self.params.get("status", ""),
                   "stale": "true" if self.params.get("stale") else ""}
        qs = self.scoped("devices", filters)
        qs = qs.order_by("-created_at", "-pk") if hasattr(qs, "order_by") else qs
        page = paginate(qs, self.params)
        stale_after = self.stale_after()
        rows = []
        for d in DeviceSerializer(page.object_list, many=True).data:
            since = hours_since(d["last_sync_at"] or d["created_at"]) or 0
            rows.append({**d, "role_label": ROLE_LABELS.get(d["device_role"], d["device_role"]),
                         "is_stale": d["status"] == "active" and since > stale_after})
        return {"page": page, "rows": rows, "filters": filters}


class RegisterDeviceView(ActionView):
    """RegisterButton: on success the dialog becomes the one-time token view."""

    template_name = "school/devices/_register.html"

    def dialog_context(self):
        fixed = self.request.GET.get("merchant") or self.request.POST.get("fixed_merchant") or ""
        return {"roles": [(k, v, ROLE_HELP[k]) for k, v in ROLE_LABELS.items()], "fixed_merchant": fixed,
                "merchants": approved_merchants(self)}

    def validate(self, data):
        errors = {}
        if not data.get("device_name", "").strip():
            errors["device_name"] = _("Device name") + " *"
        if data.get("device_role") == "merchant" and not data.get("merchant"):
            errors["merchant"] = _("Merchant") + " *"
        return errors

    def perform(self, data):
        body = {"device_name": data["device_name"].strip(), "device_role": data.get("device_role", "canteen")}
        if body["device_role"] == "merchant":
            body["merchant"] = data.get("merchant")
        s = DeviceRegisterSerializer(data=body)
        s.is_valid(raise_exception=True)
        return pos_services.register_device_for(self.request.user, s.validated_data)

    def success(self, result):
        return token_dialog(self.request, *result)


def token_dialog(request, device, raw_token):
    """DeviceTokenModal: the raw token, exactly once (never stored readable)."""
    base = default_device_api_base(request)
    response = render(request, "school/devices/_token.html", {
        "device": device, "token": raw_token, "base": base, "qr": qr_svg(provisioning_payload(base, raw_token))})
    response["HX-Trigger"] = '{"sd-refresh": true}'
    response["Cache-Control"] = "no-store"
    return response


class DeviceQrView(PageView):
    """Redraws the QR when the backend address is edited. The token comes
    from the open dialog in this same-origin POST and is neither stored nor
    logged."""

    def post(self, request):
        response = render(request, "school/devices/_qr.html", {
            "qr": qr_svg(provisioning_payload(request.POST.get("api_base_url", ""), request.POST.get("token", "")))})
        response["Cache-Control"] = "no-store"
        return response


class RotateTokenView(ConfirmView):
    title = gettext_lazy("Rotate device token")

    def setup_object(self):
        self.device = self.scoped_object("devices", self.kwargs["pk"])

    def get_description(self):
        return _("%(name)s's current token stops working at once. You'll see the new token once; enter it on the "
                 "device to keep it working. Unsynced sales on the device stay queued.") % {"name": self.device.device_name}

    def perform(self, data):
        return pos_services.rotate_device_token(self.request.user, self.device)

    def success(self, result):
        return token_dialog(self.request, *result)


class RevokeDeviceView(ConfirmView):
    title = gettext_lazy("Revoke device")
    color = "red"

    def setup_object(self):
        self.device = self.scoped_object("devices", self.kwargs["pk"])

    def get_description(self):
        return _("%(name)s is refused on its next request and can't be re-enabled (register a new device instead). "
                 "Do this immediately for a lost or stolen till.") % {"name": self.device.device_name}

    def perform(self, data):
        return pos_services.revoke_device(self.request.user, self.device)


# ---------------------------------------------------------------------------
# Merchants
# ---------------------------------------------------------------------------

APPROVAL_LABELS = {"approved": gettext_lazy("Approved"), "pending": gettext_lazy("Pending"),
                   "suspended": gettext_lazy("Suspended"), "none": gettext_lazy("Not requested")}


class MerchantsView(PageView):
    template_name = "school/merchants/index.html"
    regions = {"merchants_table": ("school/merchants/_table.html", "table")}

    def page_context(self):
        return {"approval_options": list(APPROVAL_LABELS.items())}

    def table(self):
        approval = self.params.get("approval", "")
        page = paginate(self.scoped("merchants").order_by("name", "pk"), self.params)
        rows = [m for m in MerchantSerializer(page.object_list, many=True, context={"request": self.request}).data
                if not approval or (m["my_school_approval"] or "none") == approval]
        return {"page": page, "rows": rows, "approval": approval}


class NewMerchantView(ActionView):
    template_name = "school/merchants/_new.html"

    def validate(self, data):
        return {} if data.get("name", "").strip() else {"name": _("Name") + " *"}

    def perform(self, data):
        s = MerchantSerializer(data={k: data.get(k, "") for k in ("name", "category", "contact_phone")},
                               context={"request": self.request})
        s.is_valid(raise_exception=True)
        return merchant_services.create_merchant(self.request.user, **s.validated_data)


class _MerchantApproval(ConfirmView):
    new_status = None

    def setup_object(self):
        self.merchant = self.scoped_object("merchants", self.kwargs["pk"])

    def perform(self, data):
        return merchant_services.set_approval(self.request.user, self.merchant, self.new_status, None)


class ApproveMerchantView(_MerchantApproval):
    new_status = "approved"
    color = "green"
    description = gettext_lazy("Your students' cards will work at this merchant's devices from their next cache "
                               "refresh. Parents can still block it per child.")

    def get_title(self):
        return _("Approve %(name)s") % {"name": self.merchant.name}


class SuspendMerchantView(_MerchantApproval):
    new_status = "suspended"
    color = "red"
    description = gettext_lazy("Your students' cards are removed from this merchant's devices at their next refresh; "
                               "later sales are rejected. Past sales and the statement stay.")

    def get_title(self):
        return _("Suspend %(name)s") % {"name": self.merchant.name}


class MerchantStatementView(PageView):
    """StatementDrawer: credits, debits, settlement balance, ledger entries."""

    def get(self, request, pk):
        merchant = self.scoped_object("merchants", pk)
        today = kampala_today()
        rng = {"from": valid_day(request.GET.get("from"), shift_day(today, -29)),
               "to": valid_day(request.GET.get("to"), today)}
        ctx = {"merchant": merchant, "range": rng}
        try:
            st = merchant_services.merchant_statement(request.user, merchant, rng)
            page = paginate(st["entries"], request.GET)
            ctx.update({"st": st, "page": page, "entries": LedgerEntrySerializer(page.object_list, many=True).data})
        except HANDLED as exc:
            ctx["error"] = as_error(exc)
        tpl = "school/merchants/_statement_body.html" if request.headers.get("HX-Target") == "statement_body" \
            else "school/merchants/_statement.html"
        return render(request, tpl, ctx)


# ---------------------------------------------------------------------------
# Products & categories
# ---------------------------------------------------------------------------

class ProductsView(PageView):
    template_name = "school/products/index.html"
    regions = {"products_table": ("school/products/_products.html", "products"),
               "categories_table": ("school/products/_categories.html", "categories")}

    def page_context(self):
        cats = self.scoped("categories")[:100]
        merchants = approved_merchants(self)
        return {"category_options": [(c.pk, c.name) for c in cats],
                "merchant_options": [(m["id"], m["name"]) for m in merchants]}

    def products(self):
        filters = {"category": self.params.get("category", ""), "merchant": self.params.get("merchant", "")}
        page = paginate(self.scoped("products", filters).order_by("name", "pk"), self.params)
        names = {m["id"]: m["name"] for m in approved_merchants(self)}
        rows = [{**p, "sold_by": (names.get(p["merchant"], f"#{p['merchant']}") if p["merchant"] else _("School canteen"))}
                for p in ProductSerializer(page.object_list, many=True).data]
        return {"products_page": page, "product_rows": rows, "filters": filters}

    def categories(self):
        page = paginate(self.scoped("categories").order_by("name", "pk"), self.params)
        return {"categories_page": page, "category_rows": ProductCategorySerializer(page.object_list, many=True).data}


class CategoryFormView(ActionView):
    template_name = "school/products/_category_form.html"
    form_fields = ("name", "is_unhealthy", "active")

    def setup_object(self):
        self.obj = self.scoped_object("categories", self.kwargs["pk"]) if "pk" in self.kwargs else None

    def dialog_context(self):
        return {"obj": self.obj}

    def validate(self, data):
        return {} if data.get("name", "").strip() else {"name": _("Name") + " *"}

    def perform(self, data):
        body = {"name": data["name"].strip(), "is_unhealthy": bool(data.get("is_unhealthy")),
                "active": bool(data.get("active"))}
        if self.obj:
            s = ProductCategorySerializer(self.obj, data=body, partial=True)
            s.is_valid(raise_exception=True)
            return update_catalog_item(self.request.user, s, "productcategory")
        s = ProductCategorySerializer(data=body)
        s.is_valid(raise_exception=True)
        return create_catalog_item(self.request.user, s, "productcategory")


class ProductFormView(ActionView):
    template_name = "school/products/_product_form.html"
    form_fields = ("name", "category", "price", "merchant", "active")

    def setup_object(self):
        self.obj = self.scoped_object("products", self.kwargs["pk"]) if "pk" in self.kwargs else None

    def dialog_context(self):
        return {"obj": self.obj, "categories": self.scoped("categories")[:100], "merchants": approved_merchants(self)}

    def validate(self, data):
        errors = {}
        if not data.get("name", "").strip():
            errors["name"] = _("Name") + " *"
        if not data.get("category"):
            errors["category"] = _("Category") + " *"
        if not is_valid_amount(data.get("price", "").strip()):
            errors["price"] = _("Enter a positive amount, e.g. 1500")
        return errors

    def perform(self, data):
        body = {"name": data["name"].strip(), "category": data["category"], "price": data["price"].strip(),
                "active": bool(data.get("active")), "merchant": data.get("merchant") or None}
        if self.obj:
            s = ProductSerializer(self.obj, data=body, partial=True)
            s.is_valid(raise_exception=True)
            return update_catalog_item(self.request.user, s, "product")
        s = ProductSerializer(data=body)
        s.is_valid(raise_exception=True)
        return create_catalog_item(self.request.user, s, "product")


class DeleteCategoryView(ConfirmView):
    title = gettext_lazy("Delete category")
    color = "red"

    def setup_object(self):
        self.obj = self.scoped_object("categories", self.kwargs["pk"])

    def get_description(self):
        return _('Delete "%(name)s"? Prefer making it inactive if products or past sales use it.') % {"name": self.obj.name}

    def perform(self, data):
        delete_catalog_item(self.request.user, self.obj, "productcategory")


class DeleteProductView(ConfirmView):
    title = gettext_lazy("Delete product")
    color = "red"

    def setup_object(self):
        self.obj = self.scoped_object("products", self.kwargs["pk"])

    def get_description(self):
        return _('Delete "%(name)s"? Prefer making it inactive: past sales keep their line items either way.') % {
            "name": self.obj.name}

    def perform(self, data):
        delete_catalog_item(self.request.user, self.obj, "product")


# ---------------------------------------------------------------------------
# Policy & settings
# ---------------------------------------------------------------------------

CAPS = ["daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "low_balance_threshold"]
LISTS = ["blocked_categories", "allowed_categories", "blocked_items", "blocked_merchants", "allowed_merchants"]
CAP_LABELS = {"daily_spend_cap": gettext_lazy("Daily spend cap"), "weekly_spend_cap": gettext_lazy("Weekly spend cap"),
              "per_transaction_cap": gettext_lazy("Per-transaction cap"), "p2p_daily_cap": gettext_lazy("P2P daily cap"),
              "low_balance_threshold": gettext_lazy("Low-balance alert level")}
LIST_LABELS = {"blocked_categories": gettext_lazy("Blocked categories"),
               "allowed_categories": gettext_lazy("Allowed categories only"),
               "blocked_items": gettext_lazy("Blocked items"), "blocked_merchants": gettext_lazy("Blocked merchants"),
               "allowed_merchants": gettext_lazy("Allowed merchants only")}
LIST_SOURCE = {"blocked_categories": "categories", "allowed_categories": "categories", "blocked_items": "products",
               "blocked_merchants": "merchants", "allowed_merchants": "merchants"}


def money_errors(data, fields, allow_empty=True):
    """MoneyInput: a decimal string, never a float; '' = no limit."""
    errors = {}
    for f in fields:
        v = (data.get(f) or "").strip()
        c = to_cents(v)
        if (v == "" and not allow_empty) or (v != "" and (c is None or c < 0)):
            errors[f] = "0.00"
    return errors


class PolicyView(PageView):
    template_name = "school/policy/index.html"
    regions = {"default_policy": ("school/policy/_default.html", "default"),
               "school_settings": ("school/policy/_settings.html", "settings"),
               "overrides_table": ("school/policy/_overrides.html", "overrides")}

    def default(self, data=None, error=None, saved=False):
        policy = self.scoped("policies", {"kind": "default"}).first()
        p = PolicySerializer(policy).data
        cat = catalogue(self.request.user)
        values = {f: (data.get(f, "") if data is not None else (p[f] or "")) for f in CAPS}
        p2p = bool(data.get("p2p_enabled")) if data is not None else p["p2p_enabled"] is not False
        lists = []
        for f in LISTS:
            chosen = [str(x) for x in (data.getlist(f) if data is not None else p[f])]
            lists.append({"name": f, "label": LIST_LABELS[f], "all_empty": f.startswith("allowed"),
                          "options": [(str(k), v, str(k) in chosen) for k, v in cat[LIST_SOURCE[f]].items()]})
        return {"policy": p, "caps": [(f, CAP_LABELS[f], values[f]) for f in CAPS], "p2p_enabled": p2p,
                "lists": lists, "policy_error": error, "field_errors": money_errors(data, CAPS) if data else {}}

    def settings(self, data=None, error=None):
        obj = school_settings_for(self.request.user, {})
        s = SchoolSettingsSerializer(obj).data
        if data is not None:
            s = {**s, "offline_spend_ceiling": data.get("offline_spend_ceiling", ""),
                 "pin_lockout_threshold": data.get("pin_lockout_threshold", ""),
                 "device_stale_after_hours": data.get("device_stale_after_hours", ""),
                 "attendance_notify_guardians": bool(data.get("attendance_notify_guardians")),
                 "attendance_on_canteen_devices": bool(data.get("attendance_on_canteen_devices"))}
        return {"settings": s, "settings_error": error}

    def overrides(self):
        page = paginate(self.scoped("policies", {"kind": "override"}).order_by("-updated_at", "-pk"), self.params)
        rows = [{**p, "blocks": len(p["blocked_items"]) + len(p["blocked_categories"]) + len(p["blocked_merchants"])}
                for p in PolicySerializer(page.object_list, many=True).data]
        return {"page": page, "rows": rows}


class SaveDefaultPolicyView(PolicyView):
    def post(self, request):
        self.params = request.GET
        data = request.POST
        errors = money_errors(data, CAPS)
        if errors:
            return render(request, "school/policy/_default.html", self.default(data))
        policy = self.scoped("policies", {"kind": "default"}).first()
        body = {"p2p_enabled": bool(data.get("p2p_enabled"))}
        for f in CAPS:
            body[f] = data.get(f, "").strip() or None
        for f in LISTS:
            body[f] = [int(x) for x in data.getlist(f)]
        try:
            s = PolicySerializer(policy, data=body, partial=True, context={"request": request})
            s.is_valid(raise_exception=True)
            update_policy(request.user, s)
        except HANDLED as exc:
            return render(request, "school/policy/_default.html", self.default(data, as_error(exc)))
        response = render(request, "school/policy/_default.html", self.default())
        response["HX-Trigger"] = '{"sd-toast": {"message": "%s"}}' % _("Saved")
        return response


class SaveSchoolSettingsView(PolicyView):
    def post(self, request):
        self.params = request.GET
        data = request.POST
        body = {"offline_spend_ceiling": data.get("offline_spend_ceiling", "").strip(),
                "pin_lockout_threshold": data.get("pin_lockout_threshold"),
                "device_stale_after_hours": data.get("device_stale_after_hours"),
                "attendance_notify_guardians": bool(data.get("attendance_notify_guardians")),
                "attendance_on_canteen_devices": bool(data.get("attendance_on_canteen_devices"))}
        try:
            obj = school_settings_for(request.user, {}, write=True)
            s = SchoolSettingsSerializer(obj, data=body, partial=True)
            s.is_valid(raise_exception=True)
            update_school_settings(request.user, s)
        except HANDLED as exc:
            return render(request, "school/policy/_settings.html", self.settings(data, as_error(exc)))
        response = render(request, "school/policy/_settings.html", self.settings())
        response["HX-Trigger"] = '{"sd-toast": {"message": "%s"}}' % _("Saved")
        return response


class RemoveOverrideView(ConfirmView):
    title = gettext_lazy("Remove override")
    color = "red"

    def setup_object(self):
        self.policy = self.scoped_object("policies", self.kwargs["pk"], {"kind": "override"})

    def get_description(self):
        return _("%(name)s goes back to the school defaults, including any limits a parent set.") % {
            "name": self.policy.student.name if self.policy.student else ""}

    def perform(self, data):
        from policies.services import delete_policy

        delete_policy(self.request.user, self.policy)


# ---------------------------------------------------------------------------
# Staff accounts
# ---------------------------------------------------------------------------

STAFF_ROLE_LABELS = {"school_admin": gettext_lazy("School admin"), "canteen_staff": gettext_lazy("Canteen staff"),
                     "merchant_staff": gettext_lazy("Merchant staff"), "student": gettext_lazy("Student portal")}
STAFF_ROLE_HELP = {
    "canteen_staff": gettext_lazy("Uses the POS app at the canteen. Can't sign in to this dashboard."),
    "merchant_staff": gettext_lazy("Linked to one approved merchant; sees that merchant's statement."),
    "school_admin": gettext_lazy("Full access to this school's dashboard."),
}


class StaffView(PageView):
    template_name = "school/staff/index.html"
    regions = {"staff_table": ("school/staff/_table.html", "table")}

    def page_context(self):
        return {"role_options": list(STAFF_ROLE_LABELS.items())}

    def table(self):
        filters = {"role": self.params.get("role", "")}
        page = paginate(self.scoped("staff", filters), self.params)
        rows = [{**u, "role_label": STAFF_ROLE_LABELS.get(u["role"], u["role"])}
                for u in StaffUserSerializer(page.object_list, many=True).data]
        return {"page": page, "rows": rows, "filters": filters}


class NewStaffView(ActionView):
    template_name = "school/staff/_new.html"

    def dialog_context(self):
        return {"roles": [(r, STAFF_ROLE_LABELS[r], STAFF_ROLE_HELP[r]) for r in ("canteen_staff", "merchant_staff",
                                                                                  "school_admin")],
                "merchants": approved_merchants(self)}

    def validate(self, data):
        errors = {}
        if not data.get("email", "").strip():
            errors["email"] = _("Email") + " *"
        if len(data.get("password", "")) < 8:
            errors["password"] = _("At least 8 characters. Share it privately.")
        if data.get("role") == "merchant_staff" and not data.get("merchant"):
            errors["merchant"] = _("Merchant") + " *"
        return errors

    def perform(self, data):
        body = {k: data.get(k, "").strip() for k in ("email", "full_name", "phone_number", "role")}
        body["password"] = data.get("password", "")
        if body["role"] == "merchant_staff":
            body["merchant"] = data.get("merchant")
        s = StaffUserSerializer(data=body)
        s.is_valid(raise_exception=True)
        return create_staff_from(self.request.user, s.validated_data)


class ToggleStaffView(ConfirmView):
    def setup_object(self):
        self.user = self.scoped_object("staff", self.kwargs["pk"])
        self.color = "red" if self.user.is_active else "green"

    def get_title(self):
        return _("Deactivate") if self.user.is_active else _("Reactivate")

    def get_description(self):
        if self.user.is_active:
            return _("%(email)s can't sign in any more. Nothing they recorded is deleted.") % {"email": self.user.email}
        return _("%(email)s can sign in again.") % {"email": self.user.email}

    def perform(self, data):
        return update_staff_user(self.request.user, self.user, {"is_active": not self.user.is_active})


class SetStaffPasswordView(ActionView):
    template_name = "school/staff/_password.html"

    def setup_object(self):
        self.user = self.scoped_object("staff", self.kwargs["pk"])

    def dialog_context(self):
        return {"target": self.user}

    def validate(self, data):
        return {} if len(data.get("password", "")) >= 8 else {"password": _("At least 8 characters. Share it privately.")}

    def perform(self, data):
        s = SetPasswordSerializer(data={"password": data["password"]})
        s.is_valid(raise_exception=True)
        return set_staff_password(self.request.user, self.user, s.validated_data["password"])

    def success(self, result):
        return hx_done(_("Done"), refresh=False)

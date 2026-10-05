from django.contrib.auth import logout
from django.shortcuts import redirect, render
from django.utils.translation import gettext as _
from django.views import View

from . import scoping
from .errors import HANDLED, as_error
from .htmx import hx_done, hx_redirect, hx_target, is_htmx
from .roles import decide_route


class AreaRequiredMixin:
    """Route protection (was src/proxy.ts + lib/roles.ts): signed-out users go
    to /login?next=, users of another area to their home, and roles that
    don't use the web (parents, canteen/merchant staff) are refused."""

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        role = user.role if user.is_authenticated else None
        decision = decide_route(role, request.path)
        if decision.kind == "redirect":
            if role is None and is_htmx(request):
                return hx_redirect("/login?expired=1")
            return redirect(decision.to)
        if decision.kind == "refuse":
            logout(request)
            return redirect("/login?refused=1")
        return super().dispatch(request, *args, **kwargs)


class TenantScopedMixin:
    """Every web queryset goes through web.core.scoping (the API's own scoping)."""

    def scoped(self, name, params=None):
        return scoping.scoped(self.request.user, name, params)

    def scoped_object(self, name, pk, params=None):
        return scoping.scoped_object(self.request.user, name, pk, params)


class PageView(AreaRequiredMixin, TenantScopedMixin, View):
    """A page made of regions. A full GET renders every region; an HTMX GET
    whose HX-Target names a region renders only that region (filters, paging,
    tabs) -- the HTMX twin of the React page re-fetching one list."""

    template_name = None
    # region id (the HTML id HTMX targets) -> (partial template, method name)
    regions: dict = {}
    # regions computed for a full page (default: all of them)
    page_regions = None

    def page_context(self):
        return {}

    def _region(self, region_id):
        tpl, method = self.regions[region_id]
        try:
            return getattr(self, method)()
        except HANDLED as exc:
            return {"errors": {region_id: as_error(exc)}}

    def get(self, request, *args, **kwargs):
        self.params = request.GET
        target = hx_target(request)
        if target in self.regions:
            ctx = {"view": self, **self.page_context(), **self._region(target)}
            return render(request, self.regions[target][0], ctx)
        ctx = {"view": self, **self.page_context()}
        errors = {}
        for region_id in self.page_regions or self.regions:
            data = self._region(region_id)
            errors.update(data.pop("errors", {}))
            ctx.update(data)
        ctx["errors"] = errors
        return render(request, self.template_name, ctx)


class ActionView(AreaRequiredMixin, TenantScopedMixin, View):
    """The ConfirmAction / form-dialog pattern. GET renders the dialog body;
    POST runs `perform()` through the service layer and answers with HTMX
    events (close, toast, refresh), or with the dialog again showing the
    backend's own error."""

    template_name = "core/components/confirm_action.html"
    success_message = None  # default: "Done"

    def setup_object(self):
        """Load the object(s) the action is about (scoped) into self."""

    def dialog_context(self):
        return {}

    def perform(self, data):
        raise NotImplementedError

    def success(self, result):
        return hx_done(self.success_message or _("Done"))

    def render_dialog(self, extra=None):
        ctx = {"view": self, "action_url": self.request.path, **self.dialog_context(), **(extra or {})}
        return render(self.request, self.template_name, ctx)

    def get(self, request, *args, **kwargs):
        self.setup_object()
        return self.render_dialog({"data": request.GET})

    def post(self, request, *args, **kwargs):
        self.setup_object()
        data = request.POST
        field_errors = self.validate(data)
        if field_errors:
            return self.render_dialog({"data": data, "field_errors": field_errors})
        try:
            result = self.perform(data)
        except HANDLED as exc:
            return self.render_dialog({"data": data, "error": as_error(exc)})
        return self.success(result)

    def validate(self, data):
        """Client-side checks the React form did (required fields, PIN
        repeat…) -> {field: message}; empty when valid."""
        return {}

from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext as _
from django.views import View
from rest_framework.exceptions import Throttled
from rest_framework_simplejwt.serializers import TokenObtainSerializer

from accounts.services import set_preferred_language
from core.throttles import AuthThrottle
from notifications import services as notification_services

from .mixins import AreaRequiredMixin, TenantScopedMixin
from .roles import home_for

LANGUAGES = [("en", "English"), ("lg", "Luganda"), ("sw", "Kiswahili")]


def set_language_cookie(response, language):
    response.set_cookie(settings.LANGUAGE_COOKIE_NAME, language, max_age=365 * 86400, samesite="Lax",
                        secure=settings.SESSION_COOKIE_SECURE)
    return response


class HomeRedirectView(AreaRequiredMixin, View):
    """`/`: signed-in users to their home (the mixin redirects), else /login."""

    def get(self, request):
        return redirect("/login")


class LoginView(View):
    """/login (was app/login/page.tsx + POST /api/auth/login)."""

    template_name = "core/login.html"

    def get(self, request):
        refused = request.GET.get("refused") == "1"
        expired = request.GET.get("expired") == "1"
        if refused or expired:
            # a refused role or an ended session must not leave a session behind
            logout(request)
        return render(request, self.template_name, {"refused": refused, "expired": expired, "email": ""})

    def post(self, request):
        email = (request.POST.get("email") or "").strip()
        password = request.POST.get("password") or ""
        ctx = {"refused": False, "expired": False, "email": email}
        throttle = AuthThrottle()
        if not throttle.allow_request(request, None):
            ctx["error"] = Throttled(throttle.wait()).detail
            return render(request, self.template_name, ctx, status=429)
        user = authenticate(request, username=email, password=password)
        if user is None:
            ctx["error"] = TokenObtainSerializer.default_error_messages["no_active_account"]
            return render(request, self.template_name, ctx, status=401)
        home = home_for(user.role)
        if not home:
            # parents -> mobile app; canteen/merchant staff -> POS app. No session.
            ctx["error"] = (_("Parents use the SchoolDimes mobile app, not this dashboard.") if user.role == "parent"
                            else _("This account can't use the web dashboard. Canteen and merchant staff use the "
                                   "POS app; parents use the mobile app."))
            ctx["refused_role"] = user.role
            return render(request, self.template_name, ctx, status=403)
        login(request, user)  # rotates the session id
        nxt = request.GET.get("next") or request.POST.get("next") or ""
        target = nxt if nxt.startswith(home) and url_has_allowed_host_and_scheme(nxt, {request.get_host()}) else home
        return set_language_cookie(redirect(target), user.preferred_language)


class LogoutView(View):
    def post(self, request):
        logout(request)
        return redirect("/login")


class LocaleView(View):
    """POST /locale {locale, next}: switches the UI language (cookie) and keeps
    the signed-in user's preferred_language in step (was /api/auth/locale +
    PATCH /me)."""

    def post(self, request):
        language = request.POST.get("locale")
        nxt = request.POST.get("next") or request.headers.get("Referer") or "/"
        if not url_has_allowed_host_and_scheme(nxt, {request.get_host()}):
            nxt = "/"
        response = redirect(nxt)
        if language not in dict(LANGUAGES):
            return response
        if request.user.is_authenticated:
            set_preferred_language(request.user, language)
        return set_language_cookie(response, language)


class NotificationBellView(AreaRequiredMixin, TenantScopedMixin, View):
    """The bell's popover content: unread count + the latest 8 (polled every 60 s)."""

    def get(self, request):
        return render(request, "core/components/notification_bell_body.html", bell_context(self))


class NotificationReadView(AreaRequiredMixin, TenantScopedMixin, View):
    def post(self, request, pk):
        notification_services.mark_read(self.scoped_object("notifications", pk))
        return render(request, "core/components/notification_bell_body.html", bell_context(self))


class NotificationReadAllView(AreaRequiredMixin, TenantScopedMixin, View):
    def post(self, request):
        notification_services.mark_all_read(request.user)
        return render(request, "core/components/notification_bell_body.html", bell_context(self))


def bell_context(view):
    return {
        "notifications": list(view.scoped("notifications").order_by("-created_at", "-id")[:8]),
        "unread": notification_services.unread_count(view.request.user),
    }


"""Student portal (was src/app/student/page.tsx): read-only, the signed-in
student's own summary only (students.portal.portal_summary)."""
from django.shortcuts import render
from django.views import View

from students.portal import portal_summary
from web.core.errors import HANDLED, as_error
from web.core.mixins import AreaRequiredMixin


class PortalView(AreaRequiredMixin, View):
    def get(self, request):
        try:
            ctx = {"data": portal_summary(request.user)}
        except HANDLED as exc:
            ctx = {"error": as_error(exc)}
        return render(request, "student/index.html", ctx)

from django.utils.translation import gettext as _
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ServiceError
from core.permissions import is_parent

from .services import parent_dashboard


class ParentDashboardView(APIView):
    """GET /api/v1/parent/dashboard/ -- parents only."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        if not is_parent(request.user):
            raise ServiceError("forbidden", _("Only parents have a parent dashboard."), status=403)
        return Response(parent_dashboard(request.user))

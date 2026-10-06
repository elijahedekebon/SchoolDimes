from django.db.models import Q
from rest_framework import permissions, viewsets

from core.permissions import is_platform_admin, is_school_admin

from .models import FinancialLiteracyTip
from .serializers import FinancialLiteracyTipSerializer


class FinancialLiteracyTipViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialLiteracyTipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .services import tips_for

        return tips_for(self.request.user, self.request.query_params)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), _IsAdminManagingOwnScope()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        from .services import create_tip

        create_tip(self.request.user, serializer)


class _IsAdminManagingOwnScope(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_platform_admin(request.user) or is_school_admin(request.user)

    def has_object_permission(self, request, view, obj):
        from .services import can_manage_tip

        return can_manage_tip(request.user, obj)

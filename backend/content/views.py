from django.db.models import Q
from rest_framework import permissions, viewsets

from core.permissions import is_platform_admin, is_school_admin

from .models import FinancialLiteracyTip
from .serializers import FinancialLiteracyTipSerializer


class FinancialLiteracyTipViewSet(viewsets.ModelViewSet):
    serializer_class = FinancialLiteracyTipSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = FinancialLiteracyTip.objects.select_related("school")
        language = self.request.query_params.get("language")
        if language:
            qs = qs.filter(language=language)
        if is_platform_admin(user):
            return qs
        return qs.filter(Q(school__isnull=True) | Q(school_id=user.school_id))

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [permissions.IsAuthenticated(), _IsAdminManagingOwnScope()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        if is_platform_admin(user):
            serializer.save()  # may set school=None (global) or any school
        else:
            serializer.save(school=user.school)


class _IsAdminManagingOwnScope(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_platform_admin(request.user) or is_school_admin(request.user)

    def has_object_permission(self, request, view, obj):
        if is_platform_admin(request.user):
            return True
        return is_school_admin(request.user) and obj.school_id == request.user.school_id

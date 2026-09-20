from rest_framework import permissions, viewsets

from accounts.models import User
from core.permissions import (
    IsSameSchoolObject,
    IsSchoolAdminOrPlatformAdmin,
    is_platform_admin,
)

from .models import Guardian, Student
from .serializers import GuardianSerializer, StudentSerializer


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSameSchoolObject]

    def get_queryset(self):
        user = self.request.user
        qs = Student.objects.select_related("school")
        if is_platform_admin(user):
            school_id = self.request.query_params.get("school")
            return qs.filter(school_id=school_id) if school_id else qs
        if user.role == User.Role.PARENT:
            return qs.filter(guardian_links__parent=user).distinct()
        # school_admin / canteen_staff / merchant_staff: scoped to own school
        return qs.filter(school_id=user.school_id)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsSchoolAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated(), IsSameSchoolObject()]

    def perform_create(self, serializer):
        user = self.request.user
        # tenant scoping is always derived server-side, never from client input,
        # except platform_admin who legitimately operates across tenants.
        if is_platform_admin(user):
            school = serializer.validated_data.get("school") or self.request.data.get("school")
            serializer.save(school_id=school if isinstance(school, int) else user.school_id)
        else:
            serializer.save(school=user.school)


class GuardianViewSet(viewsets.ModelViewSet):
    serializer_class = GuardianSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Guardian.objects.select_related("parent", "student")
        if is_platform_admin(user):
            return qs
        if user.role == User.Role.PARENT:
            return qs.filter(parent=user)
        return qs.filter(student__school_id=user.school_id)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsSchoolAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated()]

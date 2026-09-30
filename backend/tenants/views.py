from django.db.models import Q
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsPlatformAdmin, is_platform_admin, is_school_admin

from .models import School, SchoolReferral
from .serializers import SchoolReferralSerializer, SchoolSerializer, SchoolSettingsSerializer
from .services import apply_referral_reward


class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsPlatformAdmin]


class SchoolReferralViewSet(viewsets.ModelViewSet):
    serializer_class = SchoolReferralSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = SchoolReferral.objects.select_related("referring_school", "referred_school")
        if is_platform_admin(user):
            return qs
        if is_school_admin(user):
            return qs.filter(
                Q(referring_school_id=user.school_id) | Q(referred_school_id=user.school_id)
            )
        return qs.none()

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy", "apply"):
            return [IsPlatformAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=True, methods=["post"])
    def apply(self, request, pk=None):
        referral = self.get_object()
        apply_referral_reward(referral)
        return Response(self.get_serializer(referral).data)



class SchoolSettingsView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/v1/school-settings/ -- the caller's own school.
    school_admin (read/write), other staff (read). platform_admin must pass
    ?school=<id> (writes audit-logged)."""

    serializer_class = SchoolSettingsSerializer

    http_method_names = ["get", "patch", "put", "head", "options"]

    def get_object(self):
        from django.utils.translation import gettext as _

        from core.exceptions import ServiceError
        from students.access import STAFF_ROLES

        from .services import get_school_settings

        user = self.request.user
        if is_platform_admin(user):
            school_id = self.request.query_params.get("school")
            if not school_id:
                raise ServiceError("school_required", _("platform_admin must pass ?school=<id>."))
        elif user.role in STAFF_ROLES and user.school_id:
            school_id = user.school_id
        else:
            raise ServiceError("forbidden", _("Only school staff can see school settings."), status=403)
        if self.request.method not in permissions.SAFE_METHODS and not (
            is_platform_admin(user) or is_school_admin(user)
        ):
            raise ServiceError("forbidden", _("Only a school admin can change school settings."), status=403)
        return get_school_settings(int(school_id))

    def perform_update(self, serializer):
        from core.audit import audit

        serializer.save()
        audit(self.request.user, "school_settings.update", serializer.instance)

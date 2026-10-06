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
        from .services import referrals_for

        return referrals_for(self.request.user, self.request.query_params)

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
        from .services import school_settings_for

        return school_settings_for(self.request.user, self.request.query_params,
                                   write=self.request.method not in permissions.SAFE_METHODS)

    def perform_update(self, serializer):
        from .services import update_school_settings

        update_school_settings(self.request.user, serializer)


class MySchoolView(generics.GenericAPIView):
    """Part 4A: GET /api/v1/my-school/ -- read-only name and branding of the
    caller's own school (staff and students), so the dashboard can show the
    school's logo/colour. Parents get the schools of their linked students
    as a list under `schools`; platform_admin gets `school: null`."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from .services import my_school

        return Response(my_school(request.user))

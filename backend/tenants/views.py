from django.db.models import Q
from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from core.permissions import IsPlatformAdmin, is_platform_admin, is_school_admin

from .models import School, SchoolReferral
from .serializers import SchoolReferralSerializer, SchoolSerializer
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

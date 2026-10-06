from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.serializers import StaffUserSerializer
from core.audit import audit
from core.models import AuditLog
from core.permissions import IsPlatformAdmin
from payments.models import UnmatchedWebhook
from tenants.serializers import SchoolSerializer

from . import services
from .serializers import AuditLogSerializer, OnboardSerializer, UnmatchedWebhookSerializer


class OnboardSchoolView(APIView):
    """POST /api/v1/platform/schools/onboard/ -- platform_admin."""

    permission_classes = [IsPlatformAdmin]

    def post(self, request):
        s = OnboardSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        school, admin = services.onboard_school(
            request.user, name=d["name"], address=d.get("address", ""), branding=d.get("branding"),
            supported_languages=d.get("supported_languages"), policy=d.get("policy"),
            settings=d.get("settings"), admin=d["admin"],
        )
        return Response({"school": SchoolSerializer(school).data, "admin": StaffUserSerializer(admin).data},
                        status=status.HTTP_201_CREATED)


class SchoolStatsView(APIView):
    """GET /api/v1/platform/schools/stats/ -- platform_admin."""

    permission_classes = [IsPlatformAdmin]

    def get(self, request):
        return Response({"results": services.school_stats()})


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/v1/audit-logs/ -- platform_admin. ?school=, ?action=, ?actor=."""

    serializer_class = AuditLogSerializer
    permission_classes = [IsPlatformAdmin]

    def get_queryset(self):
        return services.audit_logs_for(self.request.user, self.request.query_params)


class UnmatchedWebhookViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/v1/payments/unmatched-webhooks/ (?reviewed=true|false),
    POST /api/v1/payments/unmatched-webhooks/{id}/mark-reviewed/ -- platform_admin."""

    serializer_class = UnmatchedWebhookSerializer
    permission_classes = [IsPlatformAdmin]

    def get_queryset(self):
        return services.unmatched_webhooks_for(self.request.user, self.request.query_params)

    @action(detail=True, methods=["post"], url_path="mark-reviewed")
    def mark_reviewed(self, request, pk=None):
        return Response(self.get_serializer(services.mark_webhook_reviewed(request.user, self.get_object())).data)

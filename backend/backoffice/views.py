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
        qs = AuditLog.objects.select_related("actor", "school").order_by("-created_at", "-id")
        p = self.request.query_params
        if p.get("school"):
            qs = qs.filter(school_id=p["school"])
        if p.get("action"):
            qs = qs.filter(action__icontains=p["action"])
        if p.get("actor"):
            qs = qs.filter(actor_id=p["actor"])
        return qs


class UnmatchedWebhookViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /api/v1/payments/unmatched-webhooks/ (?reviewed=true|false),
    POST /api/v1/payments/unmatched-webhooks/{id}/mark-reviewed/ -- platform_admin."""

    serializer_class = UnmatchedWebhookSerializer
    permission_classes = [IsPlatformAdmin]

    def get_queryset(self):
        qs = UnmatchedWebhook.objects.all()
        if self.request.query_params.get("reviewed") in ("true", "false"):
            qs = qs.filter(reviewed=self.request.query_params["reviewed"] == "true")
        return qs

    @action(detail=True, methods=["post"], url_path="mark-reviewed")
    def mark_reviewed(self, request, pk=None):
        hook = self.get_object()
        hook.reviewed = True
        hook.save(update_fields=["reviewed"])
        audit(request.user, "unmatched_webhook.reviewed", hook, force=True)
        return Response(self.get_serializer(hook).data)

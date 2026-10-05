from django.urls import re_path

from core.routers import OptionalSlashRouter

from .views import AuditLogViewSet, OnboardSchoolView, SchoolStatsView, UnmatchedWebhookViewSet

router = OptionalSlashRouter()
router.register(r"audit-logs", AuditLogViewSet, basename="auditlog")
router.register(r"payments/unmatched-webhooks", UnmatchedWebhookViewSet, basename="unmatchedwebhook")

urlpatterns = [
    re_path(r"^platform/schools/onboard/?$", OnboardSchoolView.as_view(), name="platform-onboard"),
    re_path(r"^platform/schools/stats/?$", SchoolStatsView.as_view(), name="platform-school-stats"),
] + router.urls

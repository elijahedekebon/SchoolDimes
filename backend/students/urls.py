from rest_framework.routers import DefaultRouter

from .views import GuardianViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="student")
router.register(r"guardians", GuardianViewSet, basename="guardian")

urlpatterns = router.urls

# Part 4A
from django.urls import re_path  # noqa: E402

from .views import StudentPortalView  # noqa: E402

urlpatterns = [re_path(r"^student-portal/me/?$", StudentPortalView.as_view(), name="student-portal-me")] + urlpatterns

from rest_framework.routers import DefaultRouter

from .views import SchoolReferralViewSet, SchoolViewSet

router = DefaultRouter()
router.register(r"schools", SchoolViewSet, basename="school")
router.register(r"school-referrals", SchoolReferralViewSet, basename="schoolreferral")

urlpatterns = router.urls

# Part 2
from django.urls import re_path  # noqa: E402

from .views import SchoolSettingsView  # noqa: E402

urlpatterns = [re_path(r"^school-settings/?$", SchoolSettingsView.as_view(), name="school-settings")] + urlpatterns

from rest_framework.routers import DefaultRouter

from .views import SchoolReferralViewSet, SchoolViewSet

router = DefaultRouter()
router.register(r"schools", SchoolViewSet, basename="school")
router.register(r"school-referrals", SchoolReferralViewSet, basename="schoolreferral")

urlpatterns = router.urls

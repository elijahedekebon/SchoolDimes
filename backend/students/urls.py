from rest_framework.routers import DefaultRouter

from .views import GuardianViewSet, StudentViewSet

router = DefaultRouter()
router.register(r"students", StudentViewSet, basename="student")
router.register(r"guardians", GuardianViewSet, basename="guardian")

urlpatterns = router.urls

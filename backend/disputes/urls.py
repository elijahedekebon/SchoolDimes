from core.routers import OptionalSlashRouter

from .views import DisputeViewSet

router = OptionalSlashRouter()
router.register(r"disputes", DisputeViewSet, basename="dispute")

urlpatterns = router.urls

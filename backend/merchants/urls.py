from core.routers import OptionalSlashRouter

from .views import MerchantViewSet

router = OptionalSlashRouter()
router.register(r"merchants", MerchantViewSet, basename="merchant")

urlpatterns = router.urls

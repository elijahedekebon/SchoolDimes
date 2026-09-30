from core.routers import OptionalSlashRouter

from .views import PooledFundViewSet

router = OptionalSlashRouter()
router.register(r"pooled-funds", PooledFundViewSet, basename="pooledfund")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from .views import FinancialLiteracyTipViewSet

router = DefaultRouter()
router.register(r"financial-literacy-tips", FinancialLiteracyTipViewSet, basename="tip")

urlpatterns = router.urls

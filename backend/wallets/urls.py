from rest_framework.routers import DefaultRouter

from .views import SavingsGoalViewSet, WalletViewSet

router = DefaultRouter()
router.register(r"wallets", WalletViewSet, basename="wallet")
router.register(r"savings-goals", SavingsGoalViewSet, basename="savingsgoal")

urlpatterns = router.urls

from rest_framework.routers import DefaultRouter

from .views import P2PAlertViewSet, SavingsGoalViewSet, WalletViewSet

router = DefaultRouter()
router.register(r"wallets", WalletViewSet, basename="wallet")
router.register(r"savings-goals", SavingsGoalViewSet, basename="savingsgoal")
router.register(r"p2p-alerts", P2PAlertViewSet, basename="p2palert")

urlpatterns = router.urls

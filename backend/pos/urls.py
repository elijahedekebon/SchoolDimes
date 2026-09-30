from django.urls import re_path

from core.routers import OptionalSlashRouter

from . import views

router = OptionalSlashRouter()
router.register(r"pos/devices", views.DeviceViewSet, basename="device")
router.register(r"pos/transactions", views.PosTransactionViewSet, basename="postransaction")
router.register(r"pos/shortfalls", views.ShortfallViewSet, basename="posshortfall")

urlpatterns = [
    re_path(r"^pos/cache/?$", views.PosCacheView.as_view(), name="pos-cache"),
    re_path(r"^pos/sync/?$", views.PosSyncView.as_view(), name="pos-sync"),
    re_path(r"^pos/purchase/?$", views.PosPurchaseView.as_view(), name="pos-purchase"),
    re_path(r"^pos/p2p-transfer/?$", views.PosP2PView.as_view(), name="pos-p2p"),
] + router.urls

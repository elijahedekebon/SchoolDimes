from django.urls import re_path

from core.routers import OptionalSlashRouter

from . import views

router = OptionalSlashRouter()
router.register(r"payments/deposits", views.DepositViewSet, basename="deposit")
router.register(r"payments/topup-links", views.TopUpLinkViewSet, basename="topuplink")
router.register(r"payments/gift-vouchers", views.GiftVoucherViewSet, basename="giftvoucher")
router.register(r"payments/recurring-topups", views.RecurringTopUpViewSet, basename="recurringtopup")
router.register(r"payments/payouts", views.PayoutViewSet, basename="payout")  # Part 4A

urlpatterns = [
    re_path(r"^payments/webhook/?$", views.PaymentWebhookView.as_view(), name="payment-webhook"),
    re_path(r"^public/topup-links/(?P<token>[\w-]+)/?$", views.PublicTopUpLinkView.as_view(), name="public-topup-link"),
    re_path(
        r"^public/topup-links/(?P<token>[\w-]+)/deposits/?$",
        views.PublicTopUpDepositView.as_view(),
        name="public-topup-deposit",
    ),
    re_path(
        r"^public/topup-links/(?P<token>[\w-]+)/deposits/(?P<reference>[\w-]+)/?$",
        views.PublicTopUpDepositStatusView.as_view(),
        name="public-topup-deposit-status",
    ),
    re_path(
        r"^public/topup-links/(?P<token>[\w-]+)/gift-vouchers/?$",
        views.PublicGiftVoucherView.as_view(),
        name="public-gift-voucher",
    ),
] + router.urls

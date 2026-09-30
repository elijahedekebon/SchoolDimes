from django.urls import re_path

from core.routers import OptionalSlashRouter

from . import views

router = OptionalSlashRouter()
router.register(r"fee-categories", views.FeeCategoryViewSet, basename="feecategory")
router.register(r"fees/payments", views.FeePaymentViewSet, basename="feepayment")

urlpatterns = [re_path(r"^fees/pay/?$", views.PayFeeView.as_view(), name="fee-pay")] + router.urls

from django.urls import re_path

from core.routers import OptionalSlashRouter

from . import views

router = OptionalSlashRouter()
router.register(r"notifications/push-tokens", views.PushTokenViewSet, basename="pushtoken")
router.register(r"notifications", views.NotificationViewSet, basename="notification")

urlpatterns = [
    re_path(r"^notifications/preferences/?$", views.PreferenceView.as_view(), name="notification-preferences"),
] + router.urls

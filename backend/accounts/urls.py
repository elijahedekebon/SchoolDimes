from django.urls import path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import GuardianVerificationViewSet, LoginView, LogoutView, MeView

router = DefaultRouter()
router.register(
    r"guardian-verifications", GuardianVerificationViewSet, basename="guardianverification"
)

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("auth/refresh", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("me", MeView.as_view(), name="me"),
] + router.urls

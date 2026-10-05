from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from core.permissions import is_platform_admin, is_school_admin
from core.throttles import AuthThrottle

from .models import GuardianVerification, User
from .serializers import (
    CustomTokenObtainPairSerializer,
    GuardianVerificationSerializer,
    UserSerializer,
)


class LoginView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    # Part 4A: per-IP rate limit (AUTH_THROTTLE_RATE) against password guessing.
    throttle_classes = [AuthThrottle]


class LogoutView(APIView):
    """Blacklists the given refresh token, ending that session."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "refresh token is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except TokenError:
            return Response(
                {"detail": "invalid or already-blacklisted token"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_205_RESET_CONTENT)


class MeView(generics.RetrieveUpdateAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class GuardianVerificationViewSet(viewsets.ModelViewSet):
    serializer_class = GuardianVerificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = GuardianVerification.objects.select_related("parent")
        if is_platform_admin(user):
            return qs
        if is_school_admin(user):
            # a school admin may review verifications for any parent
            # linked (via Guardian) to a student in their own school.
            from students.models import Guardian

            parent_ids = Guardian.objects.filter(
                student__school_id=user.school_id
            ).values_list("parent_id", flat=True)
            return qs.filter(parent_id__in=parent_ids)
        return qs.filter(parent=user)

    def perform_update(self, serializer):
        # only school/platform admins may change the review status;
        # a parent may only edit their own submission while still pending.
        user = self.request.user
        instance = self.get_object()
        if "status" in serializer.validated_data and not (
            is_platform_admin(user) or is_school_admin(user)
        ):
            serializer.validated_data.pop("status")
        if instance.parent_id == user.id and instance.status != GuardianVerification.Status.PENDING:
            raise permissions.PermissionDenied(
                "Cannot edit a verification that has already been reviewed."
            )
        serializer.save()

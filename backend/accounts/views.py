from django.utils.translation import gettext as _
from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import action
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
    GuardianVerificationReviewSerializer,
    GuardianVerificationSerializer,
    UserLookupSerializer,
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

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        """Part 4A: POST /guardian-verifications/{id}/review/
        {"status": "verified"|"rejected", "review_notes": "..."} -- school_admin
        (verifications of parents linked to their school) or platform_admin."""
        from core.exceptions import ServiceError

        from .services import review_guardian_verification

        if not (is_platform_admin(request.user) or is_school_admin(request.user)):
            raise ServiceError("forbidden", _("Only school or platform admins review verifications."), status=403)
        verification = self.get_object()
        s = GuardianVerificationReviewSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        review_guardian_verification(
            verification, reviewer=request.user, status=s.validated_data["status"],
            notes=s.validated_data.get("review_notes", ""),
        )
        return Response(GuardianVerificationSerializer(verification).data)


class UserLookupView(APIView):
    """Part 4A: GET /users/lookup/?email=<exact> -- school_admin/platform_admin
    find a parent account by its exact email to link it as a guardian. Exact
    match only (no listing or partial search), so admins can't enumerate the
    platform's parents. Unknown or non-parent -> 404."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from core.exceptions import ServiceError

        if not (is_platform_admin(request.user) or is_school_admin(request.user)):
            raise ServiceError("forbidden", _("Only admins can look up accounts."), status=403)
        email = (request.query_params.get("email") or "").strip()
        user = User.objects.filter(email__iexact=email, role=User.Role.PARENT, is_active=True).first() if email else None
        if user is None:
            raise ServiceError("not_found", _("No parent account with that email."), status=404)
        return Response(UserLookupSerializer(user).data)

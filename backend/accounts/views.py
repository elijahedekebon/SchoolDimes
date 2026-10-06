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
    RegisterSerializer,
    SetPasswordSerializer,
    StaffUserSerializer,
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
        from .services import verifications_for

        return verifications_for(self.request.user, self.request.query_params)

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
        from .services import lookup_parent

        return Response(UserLookupSerializer(lookup_parent(request.user, request.query_params.get("email"))).data)


class StaffUserViewSet(viewsets.ModelViewSet):
    """Part 4A: GET/POST /users/, GET/PATCH /users/{id}/,
    POST /users/{id}/set-password/ -- school_admin (own school) and
    platform_admin (audit-logged). Parents are never listed here."""

    serializer_class = StaffUserSerializer
    permission_classes = [permissions.IsAuthenticated]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def initial(self, request, *args, **kwargs):
        super().initial(request, *args, **kwargs)
        from core.exceptions import ServiceError

        if not (is_platform_admin(request.user) or is_school_admin(request.user)):
            raise ServiceError("forbidden", _("Only admins manage staff accounts."), status=403)

    def get_queryset(self):
        from .services import staff_for

        return staff_for(self.request.user, self.request.query_params)

    def create(self, request, *args, **kwargs):
        from .services import create_staff_from

        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        user = create_staff_from(request.user, s.validated_data)
        return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """Editable: full_name, phone_number, preferred_language, is_active."""
        from .services import update_staff_user

        return Response(self.get_serializer(update_staff_user(request.user, self.get_object(), request.data)).data)

    @action(detail=True, methods=["post"], url_path="set-password")
    def set_password(self, request, pk=None):
        from .services import set_staff_password

        user = self.get_object()
        s = SetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        set_staff_password(request.user, user, s.validated_data["password"])
        return Response({"detail": _("Password updated.")})


class RegisterView(APIView):
    """Part 4A: POST /api/v1/auth/register -- public, throttled. Creates a
    **parent** account (the only self-service role) and logs it in.
    Children are linked by their school (POST /guardians/)."""

    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    throttle_classes = [AuthThrottle]

    def post(self, request):
        s = RegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        user = User.objects.create_user(
            email=d["email"], password=d["password"], role=User.Role.PARENT, full_name=d["full_name"],
            phone_number=d.get("phone_number", ""), preferred_language=d.get("preferred_language", "en"),
        )
        refresh = CustomTokenObtainPairSerializer.get_token(user)
        return Response(
            {"user": UserSerializer(user).data, "access": str(refresh.access_token), "refresh": str(refresh)},
            status=status.HTTP_201_CREATED,
        )

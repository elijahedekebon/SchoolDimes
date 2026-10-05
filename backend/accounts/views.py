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
        from .services import staff_users_visible_to

        qs = staff_users_visible_to(self.request.user)
        params = self.request.query_params
        if params.get("role"):
            qs = qs.filter(role=params["role"])
        if params.get("school") and is_platform_admin(self.request.user):
            qs = qs.filter(school_id=params["school"])
        if params.get("search"):
            from django.db.models import Q

            qs = qs.filter(Q(email__icontains=params["search"]) | Q(full_name__icontains=params["search"]))
        return qs.order_by("role", "email")

    def create(self, request, *args, **kwargs):
        from core.exceptions import ServiceError
        from merchants.models import Merchant

        from .services import create_staff_user

        s = self.get_serializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        if not d.get("password"):
            raise ServiceError("password_required", _("Set an initial password (at least 8 characters)."))
        merchant = None
        if d.get("merchant"):
            merchant = Merchant.objects.filter(pk=d["merchant"]).first()
            if merchant is None:
                raise ServiceError("not_found", _("Merchant not found."), status=404)
        user = create_staff_user(
            request.user, email=d["email"], password=d["password"], role=d["role"],
            full_name=d.get("full_name", ""), phone_number=d.get("phone_number", ""),
            school_id=(d["school"].pk if d.get("school") else None), merchant=merchant,
            preferred_language=d.get("preferred_language", "en"),
        )
        return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)

    def partial_update(self, request, *args, **kwargs):
        """Editable: full_name, phone_number, preferred_language, is_active."""
        from core.audit import audit
        from core.exceptions import ServiceError

        user = self.get_object()
        allowed = {k: v for k, v in request.data.items() if k in ("full_name", "phone_number", "preferred_language", "is_active")}
        if user.pk == request.user.pk and allowed.get("is_active") is False:
            raise ServiceError("cannot_deactivate_self", _("You can't deactivate your own account."), status=409)
        s = self.get_serializer(user, data=allowed, partial=True)
        s.is_valid(raise_exception=True)
        s.save()
        audit(request.user, "user.update", user, school_id=user.school_id, details=allowed, force=True)
        return Response(s.data)

    @action(detail=True, methods=["post"], url_path="set-password")
    def set_password(self, request, pk=None):
        from core.audit import audit

        user = self.get_object()
        s = SetPasswordSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        user.set_password(s.validated_data["password"])
        user.save(update_fields=["password"])
        audit(request.user, "user.set_password", user, school_id=user.school_id, force=True)
        return Response({"detail": _("Password updated.")})

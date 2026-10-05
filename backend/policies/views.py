from django.db.models import Q
from django.utils.translation import gettext as _
from rest_framework import permissions, viewsets

from accounts.models import User
from core.audit import AuditPlatformAdminWritesMixin, audit
from core.exceptions import ServiceError
from core.permissions import is_platform_admin, is_school_admin
from students.access import STAFF_ROLES, is_guardian, linked_student_ids, user_school_ids

from .models import Policy, Product, ProductCategory
from .serializers import PolicySerializer, ProductCategorySerializer, ProductSerializer
from .services import get_school_policy, validate_override_tightens


class _SchoolCatalogViewSet(AuditPlatformAdminWritesMixin, viewsets.ModelViewSet):
    """Readable by anyone attached to the school (staff, guardians);
    writable by that school's school_admin (platform_admin: audit-logged)."""

    model = None

    def get_queryset(self):
        user = self.request.user
        qs = self.model.objects.all()
        if not is_platform_admin(user):
            qs = qs.filter(school_id__in=user_school_ids(user))
        if self.request.query_params.get("active") in ("true", "false"):
            qs = qs.filter(active=self.request.query_params["active"] == "true")
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [_IsSchoolAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated()]

    def _school_id(self, serializer):
        user = self.request.user
        if is_platform_admin(user):
            school_id = self.request.data.get("school")
            if not school_id:
                raise ServiceError("school_required", _("platform_admin must pass school."))
            return int(school_id)
        return user.school_id

    def perform_create(self, serializer):
        school_id = self._school_id(serializer)
        self._check_refs(serializer, school_id)
        serializer.save(school_id=school_id)
        audit(self.request.user, f"{self.basename}.create", serializer.instance)

    def perform_update(self, serializer):
        self._check_refs(serializer, serializer.instance.school_id)
        super().perform_update(serializer)

    def _check_refs(self, serializer, school_id):
        pass


class _IsSchoolAdminOrPlatformAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_school_admin(request.user) or is_platform_admin(request.user)


class ProductCategoryViewSet(_SchoolCatalogViewSet):
    model = ProductCategory
    serializer_class = ProductCategorySerializer


class ProductViewSet(_SchoolCatalogViewSet):
    model = Product
    serializer_class = ProductSerializer

    def get_queryset(self):
        qs = super().get_queryset().select_related("category")
        if self.request.query_params.get("category"):
            qs = qs.filter(category_id=self.request.query_params["category"])
        if self.request.query_params.get("merchant"):
            qs = qs.filter(merchant_id=self.request.query_params["merchant"])
        return qs

    def _check_refs(self, serializer, school_id):
        category = serializer.validated_data.get("category")
        if category is not None and category.school_id != school_id:
            raise ServiceError("category_invalid", _("That category belongs to another school."))
        merchant = serializer.validated_data.get("merchant")
        if merchant is not None:
            from merchants.services import is_approved_for

            if not is_approved_for(merchant, school_id):
                raise ServiceError("merchant_not_approved", _("That merchant is not approved for this school."))


class PolicyViewSet(AuditPlatformAdminWritesMixin, viewsets.ModelViewSet):
    """
    School default (student=null) + per-student overrides.
      school_admin: read all of their school's policies; write the default
                    and any override in their school.
      parent:       read the school default(s) and overrides of linked
                    students; create/update/delete overrides for linked
                    students only, and only to TIGHTEN (400 policy_cannot_loosen).
      staff:        read-only, own school.
    """

    serializer_class = PolicySerializer
    http_method_names = ["get", "post", "patch", "put", "delete", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = Policy.objects.prefetch_related("blocked_categories", "allowed_categories", "blocked_items",
                                             "blocked_merchants", "allowed_merchants")
        # Part 4A list filters: ?student=<id>, ?kind=default|override.
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("kind") == "default":
            qs = qs.filter(student__isnull=True)
        elif params.get("kind") == "override":
            qs = qs.filter(student__isnull=False)
        if is_platform_admin(user):
            return qs
        if user.role == User.Role.PARENT:
            for school_id in user_school_ids(user):
                get_school_policy(school_id)
            return qs.filter(
                Q(student_id__in=linked_student_ids(user)) | Q(student__isnull=True, school_id__in=user_school_ids(user))
            )
        if user.role in STAFF_ROLES and user.school_id:
            get_school_policy(user.school_id)
            return qs.filter(school_id=user.school_id)
        return qs.none()

    def _authorize_write(self, student, school_id):
        user = self.request.user
        if is_platform_admin(user):
            return
        if is_school_admin(user) and user.school_id == school_id:
            return
        if student is not None and is_guardian(user, student):
            return
        raise ServiceError("forbidden", _("You cannot change this policy."), status=403)

    def _check_refs(self, data, school_id):
        for f in ("blocked_categories", "allowed_categories", "blocked_items"):
            for obj in data.get(f) or []:
                if obj.school_id != school_id:
                    raise ServiceError("reference_invalid", _("A referenced category or item belongs to another school."))
        from merchants.services import is_approved_for

        for f in ("blocked_merchants", "allowed_merchants"):
            for merchant in data.get(f) or []:
                if not is_approved_for(merchant, school_id):
                    raise ServiceError("reference_invalid", _("A referenced merchant is not approved for this school."))

    def _tighten_check(self, data, student, instance=None):
        if student is None or not self.request.user.role == User.Role.PARENT:
            return
        merged = {f: data.get(f, getattr(instance, f, None) if instance else None)
                  for f in ("daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "p2p_enabled")}
        merged["allowed_categories"] = data.get("allowed_categories")
        validate_override_tightens(get_school_policy(student.school_id), merged)

    def perform_create(self, serializer):
        user = self.request.user
        student = serializer.validated_data.get("student")
        if student is None:
            if not is_school_admin(user):
                raise ServiceError("forbidden", _("Only a school admin can edit the school default."), status=403)
            # the default row always exists (created lazily); create = update it
            raise ServiceError("default_exists", _("The school default already exists; PATCH it instead."), status=409)
        self._authorize_write(student, student.school_id)
        if Policy.objects.filter(student=student).exists():
            raise ServiceError("override_exists", _("This student already has an override; PATCH it instead."), status=409)
        self._check_refs(serializer.validated_data, student.school_id)
        self._tighten_check(serializer.validated_data, student)
        serializer.save(school_id=student.school_id, updated_by=user)
        audit(user, "policy.create", serializer.instance)

    def perform_update(self, serializer):
        instance = serializer.instance
        if "student" in serializer.validated_data and serializer.validated_data["student"] != instance.student:
            raise ServiceError("student_immutable", _("A policy's student cannot be changed."))
        if instance.student is None and not (is_school_admin(self.request.user) or is_platform_admin(self.request.user)):
            raise ServiceError("forbidden", _("Only a school admin can edit the school default."), status=403)
        self._authorize_write(instance.student, instance.school_id)
        self._check_refs(serializer.validated_data, instance.school_id)
        self._tighten_check(serializer.validated_data, instance.student, instance)
        serializer.save(updated_by=self.request.user)
        audit(self.request.user, "policy.update", serializer.instance)

    def perform_destroy(self, instance):
        if instance.student is None:
            raise ServiceError("forbidden", _("The school default cannot be deleted."), status=403)
        self._authorize_write(instance.student, instance.school_id)
        audit(self.request.user, "policy.destroy", instance)
        instance.delete()

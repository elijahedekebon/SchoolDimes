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
        from .services import catalog_for

        return catalog_for(self.request.user, self.model, self.request.query_params)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [_IsSchoolAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        from .services import create_catalog_item

        create_catalog_item(self.request.user, serializer, self.basename, self.request.data.get("school"))

    def perform_update(self, serializer):
        from .services import update_catalog_item

        update_catalog_item(self.request.user, serializer, self.basename)

    def perform_destroy(self, instance):
        from .services import delete_catalog_item

        delete_catalog_item(self.request.user, instance, self.basename)


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
        from .services import products_for

        return products_for(self.request.user, self.request.query_params)



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
        from .services import policies_for

        return policies_for(self.request.user, self.request.query_params)

    def perform_create(self, serializer):
        from .services import create_policy

        create_policy(self.request.user, serializer)

    def perform_update(self, serializer):
        from .services import update_policy

        update_policy(self.request.user, serializer)

    def perform_destroy(self, instance):
        from .services import delete_policy

        delete_policy(self.request.user, instance)

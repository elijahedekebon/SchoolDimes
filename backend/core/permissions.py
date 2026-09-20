"""
Shared permission classes for tenant scoping.

Tenant scoping is ALWAYS derived from the authenticated user's own
`school` (or, for parents, from the set of students they are linked to
via Guardian rows) -- never from a school id supplied by the client.
"""
from rest_framework.permissions import BasePermission, SAFE_METHODS


def is_platform_admin(user):
    return bool(user and user.is_authenticated and user.role == user.Role.PLATFORM_ADMIN)


def is_school_admin(user):
    return bool(user and user.is_authenticated and user.role == user.Role.SCHOOL_ADMIN)


def is_parent(user):
    return bool(user and user.is_authenticated and user.role == user.Role.PARENT)


class IsPlatformAdmin(BasePermission):
    message = "Only platform administrators may perform this action."

    def has_permission(self, request, view):
        return is_platform_admin(request.user)


class IsSchoolAdminOrPlatformAdmin(BasePermission):
    message = "Only school or platform administrators may perform this action."

    def has_permission(self, request, view):
        return is_school_admin(request.user) or is_platform_admin(request.user)


class IsSameSchoolObject(BasePermission):
    """
    Object-level permission for any model instance exposing `school_id`.
    platform_admin bypasses the check; everyone else must belong to the
    same school as the object.
    """

    message = "You do not have access to this school's data."

    def has_object_permission(self, request, view, obj):
        if is_platform_admin(request.user):
            return True
        obj_school_id = getattr(obj, "school_id", None)
        return obj_school_id is not None and obj_school_id == request.user.school_id


class ReadOnlyForNonAdmins(BasePermission):
    """Allow safe methods to anyone authenticated; writes require school/platform admin."""

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return is_school_admin(request.user) or is_platform_admin(request.user)

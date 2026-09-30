"""
Shared access helpers (Part 2). Tenant scope is always derived from the
authenticated identity: a staff user's own school, or for a parent the
students they're linked to via Guardian rows.
"""
from accounts.models import User
from core.permissions import is_platform_admin, is_school_admin

from .models import Guardian, Student

STAFF_ROLES = (User.Role.SCHOOL_ADMIN, User.Role.CANTEEN_STAFF, User.Role.MERCHANT_STAFF)


def is_guardian(user, student) -> bool:
    student_id = getattr(student, "pk", student)
    return bool(
        user.is_authenticated
        and user.role == User.Role.PARENT
        and Guardian.objects.filter(parent=user, student_id=student_id).exists()
    )


def linked_student_ids(user) -> list[int]:
    return list(Guardian.objects.filter(parent=user).values_list("student_id", flat=True))


def user_school_ids(user) -> list[int]:
    """Schools a (non-platform-admin) user may act in."""
    if user.role == User.Role.PARENT:
        return list(
            Student.objects.filter(guardian_links__parent=user)
            .values_list("school_id", flat=True)
            .distinct()
        )
    return [user.school_id] if user.school_id else []


def students_visible_to(user):
    qs = Student.objects.all()
    if is_platform_admin(user):
        return qs
    if user.role == User.Role.PARENT:
        return qs.filter(guardian_links__parent=user).distinct()
    if user.role in STAFF_ROLES:
        return qs.filter(school_id=user.school_id)
    return qs.none()


def can_view_student(user, student) -> bool:
    """Guardians of the student, that school's admins, platform_admin."""
    if is_platform_admin(user):
        return True
    if is_school_admin(user):
        return student.school_id == user.school_id
    return is_guardian(user, student)

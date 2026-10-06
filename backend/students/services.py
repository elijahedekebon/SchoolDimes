"""Student and guardian services shared by the API and the web pages."""
from django.db.models import Q

from accounts.models import User
from core.exceptions import ServiceError
from core.permissions import is_platform_admin


def create_student(actor, serializer, requested_school=None):
    """Saves a validated StudentSerializer in the actor's school (platform_admin
    may name one) and gives the student main + savings wallets (Part 2)."""
    from wallets.services import ensure_student_wallets

    if is_platform_admin(actor):
        school = serializer.validated_data.get("school") or requested_school
        serializer.save(school_id=school if isinstance(school, int) else actor.school_id)
    else:
        # tenant scoping is always derived server-side, never from client input
        serializer.save(school=actor.school)
    ensure_student_wallets(serializer.instance)
    return serializer.instance


def guardians_for(user, params):
    """GET /guardians/ (?student=, ?parent=): platform_admin all, parents their
    own links, staff their school's students' links."""
    from .models import Guardian

    qs = Guardian.objects.select_related("parent", "student", "parent__guardian_verification")
    for f in ("student", "parent"):
        if params.get(f):
            qs = qs.filter(**{f: params[f]})
    if is_platform_admin(user):
        return qs
    if user.role == User.Role.PARENT:
        return qs.filter(parent=user)
    return qs.filter(student__school_id=user.school_id)


def check_guardian_student(actor, student):
    """Part 4A tenant fix: a school_admin may only link students of their own school."""
    if student is not None and not is_platform_admin(actor) and student.school_id != actor.school_id:
        raise ServiceError("not_found", "Student not found.", status=404)


def p2p_history(student):
    from wallets.models import P2PTransfer

    return P2PTransfer.objects.filter(
        Q(sender_wallet__student=student) | Q(recipient_wallet__student=student)
    ).select_related("sender_wallet__student", "recipient_wallet__student")

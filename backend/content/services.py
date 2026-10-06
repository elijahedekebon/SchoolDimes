"""Financial-literacy tips, shared by the API viewset and the web pages."""
from django.db.models import Q

from core.permissions import is_platform_admin, is_school_admin

from .models import FinancialLiteracyTip


def tips_for(user, params):
    """Platform-wide tips (school=null) plus the user's school's (?language=)."""
    qs = FinancialLiteracyTip.objects.select_related("school")
    if params.get("language"):
        qs = qs.filter(language=params["language"])
    if is_platform_admin(user):
        return qs
    return qs.filter(Q(school__isnull=True) | Q(school_id=user.school_id))


def can_manage_tip(user, tip) -> bool:
    """platform_admin any tip; school_admin only their own school's."""
    if is_platform_admin(user):
        return True
    return is_school_admin(user) and tip.school_id == user.school_id


def create_tip(actor, serializer):
    if is_platform_admin(actor):
        serializer.save()  # may set school=None (global) or any school
    else:
        serializer.save(school=actor.school)
    return serializer.instance

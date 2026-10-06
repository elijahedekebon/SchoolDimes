from .models import SchoolReferral


def apply_referral_reward(referral: SchoolReferral) -> SchoolReferral:
    """
    Marks a referral as applied and flags its reward as granted.

    PLACEHOLDER: the actual reward (e.g. a billing credit or discounted
    subscription period for `referral.referring_school`) is a business/
    finance decision outside this system's scope for Part 1-4; see
    docs/DECISIONS.md. This function only records that the reward was
    triggered, so a future billing integration has a single event to key off.
    """
    referral.status = SchoolReferral.Status.APPLIED
    referral.reward_applied = True
    referral.save(update_fields=["status", "reward_applied"])
    return referral



def get_school_settings(school):
    """Returns the school's SchoolSettings row, creating it with defaults."""
    from django.db import IntegrityError, transaction

    from .models import SchoolSettings

    school_id = getattr(school, "pk", school)
    try:
        with transaction.atomic():
            return SchoolSettings.objects.get_or_create(school_id=school_id)[0]
    except IntegrityError:
        return SchoolSettings.objects.get(school_id=school_id)


def public_school(school) -> dict:
    """Part 4A: what any member of a school may see about it (name, branding)."""
    return {
        "id": school.pk,
        "name": school.name,
        "branding": school.branding or {},
        "supported_languages": school.supported_languages or [],
    }


def my_school(user) -> dict:
    """GET /my-school/ payload (and the web frame's school name/branding).
    Parents get the schools of their linked students; platform_admin none."""
    from accounts.models import User
    from students.access import user_school_ids

    from .models import School

    if user.role == User.Role.PARENT:
        schools = School.objects.filter(pk__in=user_school_ids(user)).order_by("name")
        return {"school": None, "schools": [public_school(s) for s in schools]}
    school = user.school if user.school_id else None
    return {"school": public_school(school) if school else None,
            "schools": [public_school(school)] if school else []}



def school_settings_for(user, params, *, write=False):
    """GET/PATCH /school-settings/: the caller's own school (school_admin
    read/write, other staff read); platform_admin must pass ?school=<id>."""
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin, is_school_admin
    from students.access import STAFF_ROLES

    if is_platform_admin(user):
        school_id = params.get("school")
        if not school_id:
            raise ServiceError("school_required", _("platform_admin must pass ?school=<id>."))
    elif user.role in STAFF_ROLES and user.school_id:
        school_id = user.school_id
    else:
        raise ServiceError("forbidden", _("Only school staff can see school settings."), status=403)
    if write and not (is_platform_admin(user) or is_school_admin(user)):
        raise ServiceError("forbidden", _("Only a school admin can change school settings."), status=403)
    return get_school_settings(int(school_id))


def update_school_settings(actor, serializer):
    from core.audit import audit

    serializer.save()
    audit(actor, "school_settings.update", serializer.instance)
    return serializer.instance



def schools_for(user, params=None):
    """GET /schools/ is platform_admin only."""
    from core.permissions import is_platform_admin

    from .models import School

    return School.objects.all() if is_platform_admin(user) else School.objects.none()


def referrals_for(user, params=None):
    """platform_admin: all referrals; school_admin: their school's (either side)."""
    from django.db.models import Q

    from core.permissions import is_platform_admin, is_school_admin

    from .models import SchoolReferral

    qs = SchoolReferral.objects.select_related("referring_school", "referred_school")
    if is_platform_admin(user):
        return qs
    if is_school_admin(user):
        return qs.filter(Q(referring_school_id=user.school_id) | Q(referred_school_id=user.school_id))
    return qs.none()

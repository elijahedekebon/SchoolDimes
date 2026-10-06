from django.utils import timezone


def mark_guardian_verification(verification, *, status, verified_at=None):
    """Transition a GuardianVerification to a new status. Single choke point
    so later parts (e.g. an admin review workflow) don't hand-edit the model."""
    verification.status = status
    if status == verification.Status.VERIFIED:
        verification.verified_at = verified_at or timezone.now()
    verification.save(update_fields=["status", "verified_at", "updated_at"])
    return verification


def review_guardian_verification(verification, *, reviewer, status, notes=""):
    """Part 4A: school/platform admin approves (verified) or rejects a KYC-lite
    submission, with notes. Goes through mark_guardian_verification()."""
    from core.audit import audit

    mark_guardian_verification(verification, status=status)
    if status != verification.Status.VERIFIED:
        verification.verified_at = None
    verification.review_notes = notes or ""
    verification.reviewed_by = reviewer
    verification.reviewed_at = timezone.now()
    verification.save(update_fields=["verified_at", "review_notes", "reviewed_by", "reviewed_at", "updated_at"])
    audit(reviewer, "guardian_verification.review", verification, details={"status": status})
    return verification


STAFF_CREATABLE_ROLES = ("canteen_staff", "merchant_staff", "school_admin")


def staff_users_visible_to(user):
    """Part 4A: accounts a school admin manages -- their school's canteen
    staff, school admins and student-portal logins, plus merchant staff of
    merchants approved for their school. platform_admin sees all staff."""
    from django.db.models import Q

    from core.permissions import is_platform_admin

    from .models import User

    qs = User.objects.exclude(role=User.Role.PARENT).select_related("merchant_link__merchant")
    if is_platform_admin(user):
        return qs
    return qs.filter(
        Q(school_id=user.school_id, role__in=["canteen_staff", "school_admin", "student"])
        | Q(role="merchant_staff", merchant_link__merchant__approvals__school_id=user.school_id,
            merchant_link__merchant__approvals__status="approved")
    ).distinct()


def create_staff_user(actor, *, email, password, role, full_name="", phone_number="",
                      school_id=None, merchant=None, preferred_language="en"):
    """Part 4A: school_admin creates staff for their own school; platform_admin
    for any school (school_id required). merchant_staff have no school (a
    merchant can serve several) and are linked to `merchant` in the same step."""
    from django.db import transaction
    from django.utils.translation import gettext as _

    from core.audit import audit
    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin

    from .models import User

    if role not in STAFF_CREATABLE_ROLES:
        raise ServiceError("role_invalid", _("Staff accounts can be canteen_staff, merchant_staff or school_admin."))
    if not is_platform_admin(actor):
        school_id = actor.school_id
    if role != "merchant_staff" and not school_id:
        raise ServiceError("school_required", _("A school is required for this role."))
    if role == "merchant_staff" and merchant is None:
        raise ServiceError("merchant_required", _("Merchant staff must be linked to a merchant."))
    if User.objects.filter(email__iexact=email).exists():
        raise ServiceError("email_taken", _("An account with this email already exists."), status=409)
    with transaction.atomic():
        user = User.objects.create_user(
            email=email, password=password, role=role, full_name=full_name, phone_number=phone_number,
            school_id=None if role == "merchant_staff" else school_id, preferred_language=preferred_language,
        )
        if role == "merchant_staff":
            from merchants.services import link_staff

            link_staff(actor, merchant, user)  # checks the merchant is approved for the actor's school
        audit(actor, "user.create", user, school_id=school_id, details={"role": role}, force=True)
    return user


def set_preferred_language(user, language):
    """Web language switcher (the API does the same through PATCH /me)."""
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError

    from .models import User

    if language not in User.Language.values:
        raise ServiceError("locale_invalid", _("Unknown language."))
    if user.preferred_language != language:
        user.preferred_language = language
        user.save(update_fields=["preferred_language"])
    return user



def verifications_for(user, params=None):
    """GuardianVerification rows: platform_admin all; school_admin those of
    parents linked to a student of their school; a parent their own."""
    from core.permissions import is_platform_admin, is_school_admin

    from .models import GuardianVerification

    qs = GuardianVerification.objects.select_related("parent")
    if is_platform_admin(user):
        return qs
    if is_school_admin(user):
        from students.models import Guardian

        parent_ids = Guardian.objects.filter(student__school_id=user.school_id).values_list("parent_id", flat=True)
        return qs.filter(parent_id__in=parent_ids)
    return qs.filter(parent=user)


def lookup_parent(actor, email):
    """Exact-email lookup of an active parent account (no partial search, so
    admins can't enumerate the platform's parents)."""
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin, is_school_admin

    from .models import User

    if not (is_platform_admin(actor) or is_school_admin(actor)):
        raise ServiceError("forbidden", _("Only admins can look up accounts."), status=403)
    email = (email or "").strip()
    user = User.objects.filter(email__iexact=email, role=User.Role.PARENT, is_active=True).first() if email else None
    if user is None:
        raise ServiceError("not_found", _("No parent account with that email."), status=404)
    return user

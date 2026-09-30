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

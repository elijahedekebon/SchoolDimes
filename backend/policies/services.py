from dataclasses import dataclass, field
from datetime import datetime, time, timedelta
from decimal import Decimal
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from core.exceptions import ServiceError

from .models import Policy

KAMPALA = ZoneInfo("Africa/Kampala")

REFUSAL_MESSAGES = {
    "insufficient_funds": gettext_lazy("Insufficient funds."),
    "card_frozen": gettext_lazy("This card is frozen."),
    "card_lost": gettext_lazy("This card was reported lost."),
    "no_active_card": gettext_lazy("The student has no active card."),
    "daily_cap_exceeded": gettext_lazy("Daily spending limit exceeded."),
    "weekly_cap_exceeded": gettext_lazy("Weekly spending limit exceeded."),
    "per_transaction_cap_exceeded": gettext_lazy("This purchase is above the single-purchase limit."),
    "category_blocked": gettext_lazy("This category of item is blocked for this student."),
    "category_not_allowed": gettext_lazy("This category of item is not on the student's allowed list."),
    "item_blocked": gettext_lazy("This item is blocked for this student."),
    "merchant_blocked": gettext_lazy("This merchant is blocked for this student."),
    "p2p_disabled": gettext_lazy("Transfers between students are turned off for this student."),
    "p2p_cap_exceeded": gettext_lazy("Daily transfer limit exceeded."),
    "wallet_not_spendable": gettext_lazy("Payments cannot be made from this wallet."),
}


def refusal_message(code: str) -> str:
    return str(REFUSAL_MESSAGES.get(code, code))


@dataclass
class EffectivePolicy:
    daily_spend_cap: Decimal | None = None
    weekly_spend_cap: Decimal | None = None
    per_transaction_cap: Decimal | None = None
    p2p_daily_cap: Decimal | None = None
    p2p_enabled: bool = True
    low_balance_threshold: Decimal | None = None
    blocked_category_ids: set = field(default_factory=set)
    allowed_category_ids: set | None = None  # None = no allow-list
    blocked_product_ids: set = field(default_factory=set)
    blocked_merchant_ids: set = field(default_factory=set)
    allowed_merchant_ids: set | None = None

    def to_dict(self) -> dict:
        money = lambda v: None if v is None else str(v)  # noqa: E731
        return {
            "daily_spend_cap": money(self.daily_spend_cap),
            "weekly_spend_cap": money(self.weekly_spend_cap),
            "per_transaction_cap": money(self.per_transaction_cap),
            "p2p_daily_cap": money(self.p2p_daily_cap),
            "p2p_enabled": self.p2p_enabled,
            "low_balance_threshold": money(self.low_balance_threshold),
            "blocked_category_ids": sorted(self.blocked_category_ids),
            "allowed_category_ids": None if self.allowed_category_ids is None else sorted(self.allowed_category_ids),
            "blocked_product_ids": sorted(self.blocked_product_ids),
            "blocked_merchant_ids": sorted(self.blocked_merchant_ids),
            "allowed_merchant_ids": None if self.allowed_merchant_ids is None else sorted(self.allowed_merchant_ids),
        }


def get_school_policy(school) -> Policy:
    school_id = getattr(school, "pk", school)
    try:
        with transaction.atomic():
            policy, _ = Policy.objects.get_or_create(school_id=school_id, student=None)
            return policy
    except IntegrityError:
        return Policy.objects.get(school_id=school_id, student=None)


def _ids(policy, attr):
    if policy is None or not hasattr(policy, attr):
        return set()
    return set(getattr(policy, attr).values_list("pk", flat=True))


def _tighter(a, b):
    values = [v for v in (a, b) if v is not None]
    return min(values) if values else None


def _intersect_allow(a: set, b: set):
    if a and b:
        return a & b
    if a or b:
        return a or b
    return None


def resolve(school_policy: Policy, override: Policy | None) -> EffectivePolicy:
    """Pure resolution: per-student override -> school default, tighten-only."""
    o = override
    eff = EffectivePolicy(
        daily_spend_cap=_tighter(school_policy.daily_spend_cap, o and o.daily_spend_cap),
        weekly_spend_cap=_tighter(school_policy.weekly_spend_cap, o and o.weekly_spend_cap),
        per_transaction_cap=_tighter(school_policy.per_transaction_cap, o and o.per_transaction_cap),
        p2p_daily_cap=_tighter(school_policy.p2p_daily_cap, o and o.p2p_daily_cap),
        p2p_enabled=school_policy.p2p_enabled is not False and (o is None or o.p2p_enabled is not False),
        # an alert level, not a limit: the override simply replaces it
        low_balance_threshold=(
            (o.low_balance_threshold if o and o.low_balance_threshold is not None else None)
            or school_policy.low_balance_threshold
            or Decimal(str(settings.LOW_BALANCE_DEFAULT_THRESHOLD))
        ),
        blocked_category_ids=_ids(school_policy, "blocked_categories") | _ids(o, "blocked_categories"),
        allowed_category_ids=_intersect_allow(_ids(school_policy, "allowed_categories"), _ids(o, "allowed_categories")),
        blocked_product_ids=_ids(school_policy, "blocked_items") | _ids(o, "blocked_items"),
        blocked_merchant_ids=_ids(school_policy, "blocked_merchants") | _ids(o, "blocked_merchants"),
        allowed_merchant_ids=_intersect_allow(_ids(school_policy, "allowed_merchants"), _ids(o, "allowed_merchants")),
    )
    return eff


def get_effective_policy(student) -> EffectivePolicy:
    school_policy = get_school_policy(student.school_id)
    override = Policy.objects.filter(student=student).first()
    return resolve(school_policy, override)


CAP_FIELDS = ("daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap")


def validate_override_tightens(school_policy: Policy, data: dict):
    """Parents may only tighten school limits (resolution enforces this
    anyway; this turns an attempted loosening into a clear 400)."""
    for f in CAP_FIELDS:
        value, limit = data.get(f), getattr(school_policy, f)
        if value is not None and limit is not None and value > limit:
            raise ServiceError(
                "policy_cannot_loosen",
                _("%(field)s cannot be higher than the school limit of %(limit)s.") % {"field": f, "limit": limit},
            )
    if data.get("p2p_enabled") is True and school_policy.p2p_enabled is False:
        raise ServiceError("policy_cannot_loosen", _("The school has turned transfers off."))
    school_allowed = _ids(school_policy, "allowed_categories")
    requested_allowed = {c.pk for c in data.get("allowed_categories") or []}
    if school_allowed and requested_allowed - school_allowed:
        raise ServiceError("policy_cannot_loosen", _("You can only allow categories the school allows."))


# --- spend counters (Africa/Kampala days, Monday-start weeks) ------------

def kampala_day_bounds(now=None):
    local = (now or timezone.now()).astimezone(KAMPALA)
    start = datetime.combine(local.date(), time.min, KAMPALA)
    return start, start + timedelta(days=1)


def _debit_sum(wallet, entry_types, since, until=None):
    from wallets.models import LedgerEntry

    qs = LedgerEntry.objects.filter(
        wallet=wallet, direction=LedgerEntry.Direction.DEBIT, entry_type__in=entry_types, created_at__gte=since
    )
    if until:
        qs = qs.filter(created_at__lt=until)
    return qs.aggregate(s=Sum("amount"))["s"] or Decimal("0")


def purchases_between(wallet, start, end) -> Decimal:
    """Spending that counts toward caps: the gross amount of every recorded
    sale (canteen + merchant, online + offline) whose DEVICE timestamp falls
    in [start, end) -- i.e. the day the student bought, not the day an
    offline till happened to sync. Rejected sales don't count."""
    from pos.models import PosTransaction

    return PosTransaction.objects.filter(
        wallet=wallet, sync_status__in=["applied", "shortfall"],
        device_local_timestamp__gte=start, device_local_timestamp__lt=end,
    ).aggregate(s=Sum("amount"))["s"] or Decimal("0")


def spent_today(wallet, now=None) -> Decimal:
    start, end = kampala_day_bounds(now)
    return purchases_between(wallet, start, end)


def spent_this_week(wallet, now=None) -> Decimal:
    start, end = kampala_day_bounds(now)
    return purchases_between(wallet, start - timedelta(days=start.weekday()), end)


def p2p_sent_today(wallet, now=None) -> Decimal:
    start, end = kampala_day_bounds(now)
    return _debit_sum(wallet, ["p2p_transfer_out"], start, end)



# ---------------------------------------------------------------------------
# Querysets shared by the API viewsets and the web pages
# ---------------------------------------------------------------------------

def catalog_for(user, model, params):
    """Product categories / products / fee categories: readable by anyone
    attached to the school (staff, guardians); ?active=true|false."""
    from core.permissions import is_platform_admin
    from students.access import user_school_ids

    qs = model.objects.all()
    if not is_platform_admin(user):
        qs = qs.filter(school_id__in=user_school_ids(user))
    if params.get("active") in ("true", "false"):
        qs = qs.filter(active=params["active"] == "true")
    return qs


def categories_for(user, params):
    from .models import ProductCategory

    return catalog_for(user, ProductCategory, params)


def products_for(user, params):
    """GET /products/ (?category=, ?merchant=, ?active=)."""
    from .models import Product

    qs = catalog_for(user, Product, params).select_related("category")
    if params.get("category"):
        qs = qs.filter(category_id=params["category"])
    if params.get("merchant"):
        qs = qs.filter(merchant_id=params["merchant"])
    return qs


def policies_for(user, params):
    """GET /policies/ (?student=, ?kind=default|override). Creates the school
    default lazily, as the API always has."""
    from django.db.models import Q

    from accounts.models import User
    from core.permissions import is_platform_admin
    from students.access import STAFF_ROLES, linked_student_ids, user_school_ids

    from .models import Policy

    qs = Policy.objects.prefetch_related("blocked_categories", "allowed_categories", "blocked_items",
                                         "blocked_merchants", "allowed_merchants")
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



# ---------------------------------------------------------------------------
# Catalogue and policy writes (shared by the API viewsets and the web pages)
# ---------------------------------------------------------------------------

def _check_catalog_refs(data, school_id):
    """Products: the category must be this school's, the merchant approved for it."""
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError

    category = data.get("category")
    if category is not None and getattr(category, "school_id", school_id) != school_id:
        raise ServiceError("category_invalid", _("That category belongs to another school."))
    merchant = data.get("merchant")
    if merchant is not None:
        from merchants.services import is_approved_for

        if not is_approved_for(merchant, school_id):
            raise ServiceError("merchant_not_approved", _("That merchant is not approved for this school."))


def create_catalog_item(actor, serializer, basename, requested_school=None):
    """Product categories, products, fee categories: created in the actor's
    school (platform_admin must name one)."""
    from django.utils.translation import gettext as _

    from core.audit import audit
    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin

    if is_platform_admin(actor):
        if not requested_school:
            raise ServiceError("school_required", _("platform_admin must pass school."))
        school_id = int(requested_school)
    else:
        school_id = actor.school_id
    _check_catalog_refs(serializer.validated_data, school_id)
    serializer.save(school_id=school_id)
    audit(actor, f"{basename}.create", serializer.instance)
    return serializer.instance


def update_catalog_item(actor, serializer, basename):
    from core.audit import audit

    _check_catalog_refs(serializer.validated_data, serializer.instance.school_id)
    serializer.save()
    audit(actor, f"{basename}.update", serializer.instance)
    return serializer.instance


def delete_catalog_item(actor, instance, basename):
    from core.audit import audit

    audit(actor, f"{basename}.destroy", instance)
    instance.delete()


def _authorize_policy_write(actor, student, school_id):
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin, is_school_admin
    from students.access import is_guardian

    if is_platform_admin(actor):
        return
    if is_school_admin(actor) and actor.school_id == school_id:
        return
    if student is not None and is_guardian(actor, student):
        return
    raise ServiceError("forbidden", _("You cannot change this policy."), status=403)


def _check_policy_refs(data, school_id):
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError
    from merchants.services import is_approved_for

    for f in ("blocked_categories", "allowed_categories", "blocked_items"):
        for obj in data.get(f) or []:
            if obj.school_id != school_id:
                raise ServiceError("reference_invalid", _("A referenced category or item belongs to another school."))
    for f in ("blocked_merchants", "allowed_merchants"):
        for merchant in data.get(f) or []:
            if not is_approved_for(merchant, school_id):
                raise ServiceError("reference_invalid", _("A referenced merchant is not approved for this school."))


def _tighten_check(actor, data, student, instance=None):
    if student is None or actor.role != "parent":
        return
    merged = {f: data.get(f, getattr(instance, f, None) if instance else None)
              for f in ("daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "p2p_enabled")}
    merged["allowed_categories"] = data.get("allowed_categories")
    validate_override_tightens(get_school_policy(student.school_id), merged)


def create_policy(actor, serializer):
    """Per-student overrides only (the school default always exists)."""
    from django.utils.translation import gettext as _

    from core.audit import audit
    from core.exceptions import ServiceError
    from core.permissions import is_school_admin

    from .models import Policy

    student = serializer.validated_data.get("student")
    if student is None:
        if not is_school_admin(actor):
            raise ServiceError("forbidden", _("Only a school admin can edit the school default."), status=403)
        raise ServiceError("default_exists", _("The school default already exists; PATCH it instead."), status=409)
    _authorize_policy_write(actor, student, student.school_id)
    if Policy.objects.filter(student=student).exists():
        raise ServiceError("override_exists", _("This student already has an override; PATCH it instead."), status=409)
    _check_policy_refs(serializer.validated_data, student.school_id)
    _tighten_check(actor, serializer.validated_data, student)
    serializer.save(school_id=student.school_id, updated_by=actor)
    audit(actor, "policy.create", serializer.instance)
    return serializer.instance


def update_policy(actor, serializer):
    from django.utils.translation import gettext as _

    from core.audit import audit
    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin, is_school_admin

    instance = serializer.instance
    if "student" in serializer.validated_data and serializer.validated_data["student"] != instance.student:
        raise ServiceError("student_immutable", _("A policy's student cannot be changed."))
    if instance.student is None and not (is_school_admin(actor) or is_platform_admin(actor)):
        raise ServiceError("forbidden", _("Only a school admin can edit the school default."), status=403)
    _authorize_policy_write(actor, instance.student, instance.school_id)
    _check_policy_refs(serializer.validated_data, instance.school_id)
    _tighten_check(actor, serializer.validated_data, instance.student, instance)
    serializer.save(updated_by=actor)
    audit(actor, "policy.update", serializer.instance)
    return serializer.instance


def delete_policy(actor, instance):
    from django.utils.translation import gettext as _

    from core.audit import audit
    from core.exceptions import ServiceError

    if instance.student is None:
        raise ServiceError("forbidden", _("The school default cannot be deleted."), status=403)
    _authorize_policy_write(actor, instance.student, instance.school_id)
    audit(actor, "policy.destroy", instance)
    instance.delete()

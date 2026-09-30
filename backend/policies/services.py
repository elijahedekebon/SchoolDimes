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

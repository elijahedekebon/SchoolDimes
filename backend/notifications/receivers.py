"""Signal receivers that turn ledger movements into notifications."""
from django.dispatch import receiver

from wallets.signals import ledger_entry_posted


@receiver(ledger_entry_posted)
def _savings_goal_reached(sender, entry, balance_after, **kwargs):
    wallet = entry.wallet
    if entry.direction != "credit" or wallet.wallet_type != "savings":
        return
    from wallets.savings import check_goals_reached

    # Runs inside the posting transaction, so it rolls back with the money
    # movement; notify() itself defers SMS/push I/O until commit.
    check_goals_reached(wallet)


@receiver(ledger_entry_posted)
def _low_balance(sender, entry, balance_after, **kwargs):
    """A debit on a student's MAIN wallet that crosses a guardian's alert
    level (before >= threshold > after) notifies that guardian -- at most once
    per LOW_BALANCE_ALERT_THROTTLE_HOURS per (guardian, wallet), de-duplicated
    through the Redis cache so a run of small purchases can't spam them.
    Threshold: the guardian's per-student preference, else the student's
    effective policy low_balance_threshold (else LOW_BALANCE_DEFAULT_THRESHOLD)."""
    wallet = entry.wallet
    if entry.direction != "debit" or wallet.wallet_type != "main" or wallet.student_id is None:
        return
    from decimal import Decimal
    from math import ceil

    from django.conf import settings
    from django.core.cache import cache

    from accounts.models import User
    from policies.services import get_effective_policy

    from .services import fmt_amount, get_preferences, notify

    before = balance_after + entry.amount
    student = wallet.student
    default_threshold = None
    for guardian in User.objects.filter(guardian_links__student=student, is_active=True).distinct():
        custom = get_preferences(guardian).low_balance_thresholds.get(str(student.pk))
        if custom is not None:
            threshold = Decimal(str(custom))
        else:
            if default_threshold is None:
                default_threshold = get_effective_policy(student).low_balance_threshold
            threshold = default_threshold
        if not (before >= threshold > balance_after):
            continue
        key = f"lowbal:{guardian.pk}:{wallet.pk}"
        if not cache.add(key, 1, timeout=settings.LOW_BALANCE_ALERT_THROTTLE_HOURS * 3600):
            continue
        suggested = max(Decimal("1000"), Decimal(ceil((threshold * 2 - balance_after) / 1000) * 1000))
        notify(guardian, "low_balance", {
            "student_id": student.pk, "student_name": student.name, "wallet_id": wallet.pk,
            "balance": fmt_amount(balance_after), "threshold": fmt_amount(threshold),
            "action": {"type": "top_up", "student_id": student.pk, "wallet_id": wallet.pk,
                       "suggested_amount": str(suggested)},
        })

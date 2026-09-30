"""Savings operations (Section C). Business logic only; views call these."""
import secrets

from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from core.exceptions import ServiceError
from core.money import validate_amount
from core.permissions import is_platform_admin, is_school_admin
from students.access import is_guardian

from .models import LedgerEntry, Wallet
from .services import DebitContext, DebitKind, get_student_wallet, post_transfer, require_debit


def can_operate_savings(user, student) -> bool:
    return is_guardian(user, student) or is_platform_admin(user) or (
        is_school_admin(user) and user.school_id == student.school_id
    )


def _move(debit_wallet, credit_wallet, amount, description):
    amount = validate_amount(amount)
    with transaction.atomic():
        require_debit(debit_wallet, amount, DebitContext(kind=DebitKind.SAVINGS_MOVE))
        # Part 1 convention: the debit side is always savings_move_out and the
        # credit side savings_move_in, whichever direction the money goes.
        return post_transfer(
            debit_wallet=debit_wallet,
            credit_wallet=credit_wallet,
            amount=amount,
            entry_type=LedgerEntry.EntryType.SAVINGS_MOVE_OUT,
            credit_entry_type=LedgerEntry.EntryType.SAVINGS_MOVE_IN,
            reference_id=f"savings:{secrets.token_hex(6)}",
            description=description,
        )


def move_to_savings(student, amount):
    """main -> savings (POST /wallets/{id}/savings/move-in/)."""
    return _move(get_student_wallet(student, Wallet.WalletType.MAIN),
                 get_student_wallet(student, Wallet.WalletType.SAVINGS), amount, "Moved to savings")


def move_from_savings(student, amount):
    """savings -> main (POST /wallets/{id}/savings/move-out/)."""
    return _move(get_student_wallet(student, Wallet.WalletType.SAVINGS),
                 get_student_wallet(student, Wallet.WalletType.MAIN), amount, "Moved from savings")


def set_withdrawal_window(student, start, end):
    if (start is None) != (end is None):
        raise ServiceError("window_invalid", _("Give both a start and an end, or neither to close withdrawals."))
    if start and end <= start:
        raise ServiceError("window_invalid", _("The window must end after it starts."))
    savings = get_student_wallet(student, Wallet.WalletType.SAVINGS)
    savings.withdrawal_window_start, savings.withdrawal_window_end = start, end
    savings.save(update_fields=["withdrawal_window_start", "withdrawal_window_end", "updated_at"])
    return savings


def window_is_open(savings, now=None) -> bool:
    now = now or timezone.now()
    s, e = savings.withdrawal_window_start, savings.withdrawal_window_end
    return bool(s and e and s <= now < e)


def withdraw_savings(user, student, *, amount, phone_number, idempotency_key=None):
    """Guardian-only payout of savings to mobile money, allowed only while
    the parent-configured withdrawal window is open. Debits savings now;
    a failed payout is reversed by payments (compensating entry)."""
    from payments.models import Payout
    from payments.services import initiate_payout

    if not is_guardian(user, student):
        raise ServiceError("forbidden", _("Only a guardian can withdraw savings."), status=403)
    savings = get_student_wallet(student, Wallet.WalletType.SAVINGS)
    if not window_is_open(savings):
        raise ServiceError("withdrawal_window_closed", _("Savings can only be withdrawn during the withdrawal window."), status=409)
    amount = validate_amount(amount)
    with transaction.atomic():
        require_debit(savings, amount, DebitContext(kind=DebitKind.SAVINGS_WITHDRAWAL))
    return initiate_payout(
        purpose=Payout.Purpose.SAVINGS_WITHDRAWAL,
        source_wallet=savings,
        amount=amount,
        phone_number=phone_number or user.phone_number,
        description=f"Savings withdrawal for {student.name}",
        requested_by=user,
        idempotency_key=idempotency_key,
    )


def goal_progress(goal) -> dict:
    balance = goal.wallet.cached_balance
    target = goal.target_amount
    percent = float(min(100, round(balance / target * 100, 1))) if target else None
    return {"current_amount": balance, "progress_percent": percent, "is_reached": bool(target and balance >= target)}


def check_goals_reached(savings_wallet):
    """Called after a credit to a savings wallet: stamps reached_at and
    notifies guardians once per goal."""
    from notifications.services import fmt_amount, notify_guardians

    for goal in savings_wallet.savings_goals.filter(reached_at__isnull=True, target_amount__lte=savings_wallet.cached_balance):
        goal.reached_at = timezone.now()
        goal.save(update_fields=["reached_at"])
        notify_guardians(savings_wallet.student, "savings_goal_reached", {
            "student_id": savings_wallet.student_id, "student_name": savings_wallet.student.name,
            "goal_id": goal.pk, "goal_name": goal.goal_name, "target_amount": fmt_amount(goal.target_amount),
        })

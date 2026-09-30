from django.db import IntegrityError, transaction
from django.utils.translation import gettext as _

from core.audit import audit
from core.exceptions import ServiceError
from core.money import validate_amount
from core.permissions import is_platform_admin, is_school_admin
from students.access import is_guardian
from wallets.models import LedgerEntry, Wallet
from wallets.services import (
    DebitContext,
    DebitKind,
    get_student_wallet,
    get_system_wallet,
    post_transfer,
    require_debit,
)

from .models import FeeCategory, FeePayment


def validate_category(data: dict):
    amount_type = data.get("amount_type", FeeCategory.AmountType.FIXED)
    if amount_type == FeeCategory.AmountType.FIXED:
        if not data.get("fixed_amount"):
            raise ServiceError("fee_amount_invalid", _("A fixed fee needs fixed_amount."))
        validate_amount(data["fixed_amount"])
    else:
        lo, hi = data.get("min_amount"), data.get("max_amount")
        if lo is None or hi is None or lo <= 0 or hi < lo:
            raise ServiceError("fee_amount_invalid", _("A range fee needs 0 < min_amount <= max_amount."))
        validate_amount(hi)


def pay_fee(user, *, student, fee_category, amount=None, idempotency_key=None) -> tuple[FeePayment, bool]:
    """
    Pays a fee from the student's MAIN wallet into the school settlement
    wallet (entry_type fee_payment, reference fee:<id>). Allowed for the
    student's guardians and that school's school_admin. Goes through
    authorize_debit() with kind=fee_payment: card freeze and balance apply,
    daily/weekly/per-transaction snack caps and category rules do NOT.
    Returns (payment, created).
    """
    if not (is_guardian(user, student) or is_platform_admin(user)
            or (is_school_admin(user) and user.school_id == student.school_id)):
        raise ServiceError("not_found", _("Student not found."), status=404)
    if fee_category.school_id != student.school_id:
        raise ServiceError("not_found", _("Fee category not found."), status=404)
    if not fee_category.active:
        raise ServiceError("fee_inactive", _("This fee is no longer payable."), status=409)
    if fee_category.applicable_classes and student.class_name not in fee_category.applicable_classes:
        raise ServiceError("fee_not_applicable", _("This fee does not apply to the student's class."))

    if fee_category.amount_type == FeeCategory.AmountType.FIXED:
        amount = fee_category.fixed_amount if amount in (None, "") else validate_amount(amount)
        if amount != fee_category.fixed_amount:
            raise ServiceError("fee_amount_invalid", _("This fee must be paid in full (%(amount)s).") % {"amount": fee_category.fixed_amount})
    else:
        amount = validate_amount(amount)
        if not fee_category.min_amount <= amount <= fee_category.max_amount:
            raise ServiceError("fee_amount_invalid", _("Amount must be between %(lo)s and %(hi)s.")
                               % {"lo": fee_category.min_amount, "hi": fee_category.max_amount})

    if idempotency_key:
        existing = FeePayment.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            if existing.student_id != student.pk or existing.fee_category_id != fee_category.pk or existing.amount != amount:
                raise ServiceError("idempotency_conflict", _("This idempotency_key was already used for a different request."), status=409)
            return existing, False

    wallet = get_student_wallet(student, Wallet.WalletType.MAIN)
    try:
        with transaction.atomic():
            require_debit(wallet, amount, DebitContext(kind=DebitKind.FEE_PAYMENT))
            payment = FeePayment.objects.create(
                school_id=student.school_id, student=student, fee_category=fee_category,
                amount=amount, paid_by=user, idempotency_key=idempotency_key or None,
            )
            payment.ledger_reference = f"fee:{payment.pk}"
            payment.save(update_fields=["ledger_reference"])
            post_transfer(
                debit_wallet=wallet,
                credit_wallet=get_system_wallet(student.school_id, Wallet.WalletType.SCHOOL_SETTLEMENT),
                amount=amount,
                entry_type=LedgerEntry.EntryType.FEE_PAYMENT,
                reference_id=payment.ledger_reference,
                description=f"{fee_category.name} fee",
            )
    except IntegrityError:
        existing = FeePayment.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            return existing, False
        raise
    audit(user, "fee.pay", payment)
    return payment, True

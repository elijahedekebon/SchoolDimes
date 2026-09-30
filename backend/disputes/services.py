from decimal import Decimal

from django.db import IntegrityError, transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _

from core.exceptions import InsufficientFundsError, ServiceError
from core.money import validate_amount
from core.permissions import is_school_admin
from notifications.services import notify
from pos.models import PosTransaction
from pos.services import credit_wallet_for
from students.access import is_guardian
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_student_wallet, post_transfer

from .models import OPEN_STATUSES, Dispute

# Debits a guardian may dispute through a ledger entry. POS sales are
# disputed via their PosTransaction; P2P is excluded (a refund would have to
# come out of another child's wallet -- that's a conversation, not a refund).
DISPUTABLE_ENTRY_TYPES = {LedgerEntry.EntryType.FEE_PAYMENT, LedgerEntry.EntryType.SHORTFALL_RECOVERY}


def _target_filter(dispute):
    if dispute.pos_transaction_id:
        return {"pos_transaction_id": dispute.pos_transaction_id}
    return {"ledger_entry_id": dispute.ledger_entry_id}


def original_amount(dispute) -> Decimal:
    """What was actually debited from the student for the disputed item."""
    if dispute.pos_transaction_id:
        return dispute.pos_transaction.applied_amount + dispute.pos_transaction.recovered_amount
    return dispute.ledger_entry.amount


def refunded_so_far(dispute) -> Decimal:
    return Dispute.objects.filter(
        status=Dispute.Status.RESOLVED_REFUNDED, **_target_filter(dispute)
    ).aggregate(s=Sum("refund_amount"))["s"] or Decimal("0")


def raise_dispute(user, *, reason_category, description="", pos_transaction_id=None, ledger_entry_id=None):
    if bool(pos_transaction_id) == bool(ledger_entry_id):
        raise ServiceError("target_required", _("Give exactly one of pos_transaction or ledger_entry."))
    if reason_category not in Dispute.ReasonCategory.values:
        raise ServiceError("reason_invalid", _("Unknown reason category."))
    not_found = ServiceError("not_found", _("Transaction not found."), status=404)
    if pos_transaction_id:
        txn = PosTransaction.objects.select_related("student").filter(pk=pos_transaction_id).first()
        if txn is None or txn.student is None or not is_guardian(user, txn.student):
            raise not_found
        if txn.sync_status == PosTransaction.SyncStatus.REJECTED:
            raise ServiceError("not_disputable", _("A rejected sale took no money and cannot be disputed."))
        student, school_id, target = txn.student, txn.school_id, {"pos_transaction": txn}
    else:
        entry = LedgerEntry.objects.select_related("wallet__student").filter(pk=ledger_entry_id).first()
        if entry is None or entry.wallet.student is None or not is_guardian(user, entry.wallet.student):
            raise not_found
        if entry.direction != LedgerEntry.Direction.DEBIT or entry.entry_type not in DISPUTABLE_ENTRY_TYPES:
            raise ServiceError("not_disputable", _("Only fee payments and shortfall recoveries can be disputed this way; dispute canteen sales via their POS transaction."))
        student, school_id, target = entry.wallet.student, entry.school_id, {"ledger_entry": entry}
    try:
        with transaction.atomic():
            return Dispute.objects.create(
                school_id=school_id, raised_by=user, student=student,
                reason_category=reason_category, description=description[:2000], **target,
            )
    except IntegrityError:
        raise ServiceError("dispute_already_open", _("There is already an open dispute for this transaction."), status=409)


def _notify_raiser(dispute):
    notify(dispute.raised_by, "dispute_status_changed", {
        "dispute_id": dispute.pk, "status": dispute.status, "student_id": dispute.student_id,
        "refund_amount": str(dispute.refund_amount), "notes": dispute.resolution_notes,
    })


def _require_resolver(user, dispute):
    """school_admin of the dispute's school only. platform_admin is
    deliberately excluded (proposal: disputes are resolved by the school)."""
    if not (is_school_admin(user) and user.school_id == dispute.school_id):
        raise ServiceError("forbidden", _("Only the school's admin can handle disputes."), status=403)


def start_review(user, dispute):
    _require_resolver(user, dispute)
    if dispute.status != Dispute.Status.OPEN:
        raise ServiceError("dispute_not_open", _("This dispute is not open."), status=409)
    dispute.status = Dispute.Status.UNDER_REVIEW
    dispute.save(update_fields=["status", "updated_at"])
    _notify_raiser(dispute)
    return dispute


def _refund_source_wallet(dispute) -> Wallet:
    """The wallet that received the disputed money pays the refund back."""
    if dispute.pos_transaction_id:
        txn = dispute.pos_transaction
        return credit_wallet_for(txn.device, txn.school_id)
    entry = dispute.ledger_entry
    counterpart = LedgerEntry.objects.filter(
        reference_id=entry.reference_id, direction=LedgerEntry.Direction.CREDIT, amount=entry.amount
    ).exclude(wallet_id=entry.wallet_id).select_related("wallet").first()
    if counterpart is None:
        raise ServiceError("refund_source_unknown", _("Cannot find where this payment went."), status=409)
    return counterpart.wallet


def resolve(user, dispute, *, outcome, refund_amount=None, resolution_notes=""):
    """outcome=refund: credits the student's MAIN wallet from the wallet that
    received the money (entry_type refund, reference refund:<dispute id>).
    Partial refunds allowed; total refunds on one transaction can never
    exceed the amount actually debited. outcome=deny: closes with notes."""
    _require_resolver(user, dispute)
    if dispute.status not in OPEN_STATUSES:
        raise ServiceError("dispute_not_open", _("This dispute is already resolved."), status=409)
    if outcome not in ("refund", "deny"):
        raise ServiceError("outcome_invalid", _("outcome must be refund or deny."))
    with transaction.atomic():
        dispute = Dispute.objects.select_for_update().get(pk=dispute.pk)
        if dispute.status not in OPEN_STATUSES:
            raise ServiceError("dispute_not_open", _("This dispute is already resolved."), status=409)
        # lock the disputed target so two concurrent refunds can't both pass the cap
        if dispute.pos_transaction_id:
            PosTransaction.objects.select_for_update().get(pk=dispute.pos_transaction_id)
        else:
            LedgerEntry.objects.select_for_update().get(pk=dispute.ledger_entry_id)
        dispute.resolution_notes = resolution_notes
        dispute.resolved_by, dispute.resolved_at = user, timezone.now()
        if outcome == "deny":
            dispute.status = Dispute.Status.RESOLVED_DENIED
        else:
            amount = validate_amount(refund_amount)
            remaining = original_amount(dispute) - refunded_so_far(dispute)
            if amount > remaining:
                raise ServiceError("refund_exceeds_original",
                                   _("At most %(remaining)s can still be refunded on this transaction.") % {"remaining": remaining},
                                   status=422)
            try:
                post_transfer(
                    debit_wallet=_refund_source_wallet(dispute),
                    credit_wallet=get_student_wallet(dispute.student, Wallet.WalletType.MAIN),
                    amount=amount,
                    entry_type=LedgerEntry.EntryType.REFUND,
                    reference_id=f"refund:{dispute.pk}",
                    description=f"Refund for dispute #{dispute.pk}",
                )
            except InsufficientFundsError:
                raise ServiceError("refund_source_insufficient",
                                   _("The receiving wallet no longer holds enough to refund this."), status=422)
            dispute.refund_amount = amount
            dispute.status = Dispute.Status.RESOLVED_REFUNDED
        dispute.save()
    _notify_raiser(dispute)
    return dispute

"""Student-to-student transfers + pattern alerts (Section C).

Who initiates (students have no login yet, see DECISIONS.md):
  * a guardian of the SENDER, via POST /api/v1/wallets/transfer/ (JWT);
  * the sender at a POS device, card + PIN, via POST /api/v1/pos/p2p-transfer/
    (Section D). Both call p2p_transfer() below.
"""
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from core.exceptions import ServiceError
from core.money import validate_amount
from notifications.services import fmt_amount, notify_guardians, notify_school_admins

from .models import LedgerEntry, P2PAlert, P2PTransfer, Wallet
from .services import DebitContext, DebitKind, get_student_wallet, post_transfer, require_debit


def _card_state(student):
    """(has_active_card, has_frozen_card)."""
    statuses = set(student.cards.values_list("status", flat=True))
    return "active" in statuses, "frozen" in statuses


def p2p_transfer(sender, recipient, amount, *, initiated_by=None, device=None, sender_card=None, note=""):
    amount = validate_amount(amount)
    if sender.pk == recipient.pk:
        raise ServiceError("p2p_same_student", _("A student cannot send money to themselves."))
    if sender.school_id != recipient.school_id:
        raise ServiceError("p2p_other_school", _("Transfers are only allowed within the same school."), status=422)
    active, frozen = _card_state(recipient)
    if not active or frozen:
        raise ServiceError("recipient_card_inactive", _("The recipient's card is not active."), status=422)
    if sender_card is None:
        active, frozen = _card_state(sender)
        if not active and not frozen:  # frozen -> card_frozen from require_debit
            raise ServiceError("no_active_card", _("The student has no active card."), status=422)
    from policies.services import get_effective_policy

    if not get_effective_policy(recipient).p2p_enabled:
        raise ServiceError("p2p_disabled", _("The recipient cannot receive transfers."), status=422)

    sender_wallet = get_student_wallet(sender)
    recipient_wallet = get_student_wallet(recipient)
    with transaction.atomic():
        require_debit(sender_wallet, amount, DebitContext(kind=DebitKind.P2P, card=sender_card))
        transfer = P2PTransfer.objects.create(
            school_id=sender.school_id, sender_wallet=sender_wallet, recipient_wallet=recipient_wallet,
            amount=amount, note=note[:140], initiated_by=initiated_by,
            device_id_ref=getattr(device, "pk", None),
        )
        post_transfer(
            debit_wallet=sender_wallet,
            credit_wallet=recipient_wallet,
            amount=amount,
            entry_type=LedgerEntry.EntryType.P2P_TRANSFER_OUT,
            credit_entry_type=LedgerEntry.EntryType.P2P_TRANSFER_IN,
            reference_id=f"p2p:{transfer.pk}",
            description=note[:255],
        )
        notify_guardians(recipient, "p2p_transfer_received", {
            "student_id": recipient.pk, "student_name": recipient.name,
            "sender_name": sender.name.split()[0], "amount": fmt_amount(amount), "p2p_transfer_id": transfer.pk,
        })
        evaluate_p2p_patterns(transfer)
    return transfer


def _raise_alert(student, rule, details):
    if P2PAlert.objects.filter(student=student, rule=rule, status=P2PAlert.Status.OPEN).exists():
        return None
    alert = P2PAlert.objects.create(school_id=student.school_id, student=student, rule=rule, details=details)
    notify_school_admins(student.school_id, "p2p_alert_raised", {
        "alert_id": alert.pk, "student_id": student.pk, "student_name": student.name, "rule": rule,
    })
    return alert


def evaluate_p2p_patterns(transfer: P2PTransfer) -> list:
    """
    Simple, configurable rules (settings.P2P_ALERT_*), over the last
    P2P_ALERT_WINDOW_DAYS days:
      many_distinct_senders -- recipient received from >= P2P_ALERT_DISTINCT_SENDERS
                               different students (possible pressure/extortion)
      repeated_near_cap     -- sender made >= P2P_ALERT_NEAR_CAP_COUNT transfers each
                               >= P2P_ALERT_NEAR_CAP_RATIO of their daily cap
    One OPEN alert per (student, rule) at a time.
    """
    from policies.services import get_effective_policy

    since = timezone.now() - timedelta(days=settings.P2P_ALERT_WINDOW_DAYS)
    alerts = []
    recipient = transfer.recipient_wallet.student
    senders = set(
        P2PTransfer.objects.filter(recipient_wallet=transfer.recipient_wallet, created_at__gte=since)
        .values_list("sender_wallet_id", flat=True)
    )
    if len(senders) >= settings.P2P_ALERT_DISTINCT_SENDERS:
        alerts.append(_raise_alert(recipient, P2PAlert.Rule.MANY_DISTINCT_SENDERS,
                                   {"distinct_senders": len(senders), "window_days": settings.P2P_ALERT_WINDOW_DAYS}))

    sender = transfer.sender_wallet.student
    cap = get_effective_policy(sender).p2p_daily_cap
    if cap:
        threshold = (cap * Decimal(str(settings.P2P_ALERT_NEAR_CAP_RATIO))).quantize(Decimal("0.01"))
        near = P2PTransfer.objects.filter(
            sender_wallet=transfer.sender_wallet, created_at__gte=since, amount__gte=threshold
        ).count()
        if near >= settings.P2P_ALERT_NEAR_CAP_COUNT:
            alerts.append(_raise_alert(sender, P2PAlert.Rule.REPEATED_NEAR_CAP,
                                       {"near_cap_transfers": near, "cap": str(cap), "threshold": str(threshold)}))
    return [a for a in alerts if a]


def review_alert(user, alert, status, notes=""):
    if status not in (P2PAlert.Status.REVIEWED, P2PAlert.Status.DISMISSED):
        raise ServiceError("status_invalid", _("status must be reviewed or dismissed."))
    alert.status, alert.review_notes = status, notes
    alert.reviewed_by, alert.reviewed_at = user, timezone.now()
    alert.save(update_fields=["status", "review_notes", "reviewed_by", "reviewed_at"])
    return alert


def wallet_student(wallet_id):
    wallet = Wallet.objects.select_related("student").filter(pk=wallet_id, student__isnull=False).first()
    return wallet.student if wallet else None

"""
Payments business logic. Views, Celery tasks, management commands and the
POS simulator all call these functions; none of them touch the ledger
directly. Every movement goes through wallets.services.post_transfer()
(which is two post_ledger_entry() calls).
"""
import logging
import secrets
from datetime import datetime, time, timedelta
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from core.exceptions import ServiceError
from core.money import validate_amount
from notifications.services import fmt_amount, notify, notify_guardians
from students.access import is_guardian
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_student_wallet, get_system_wallet, post_transfer

from .aggregator_client import MockAggregatorClient, WebhookEvent, get_aggregator_client
from .models import (
    Channel,
    Contributor,
    Deposit,
    GiftVoucher,
    Payout,
    RecurringTopUp,
    StudentTopUpLink,
    UnmatchedWebhook,
)
from .signals import deposit_confirmed

logger = logging.getLogger("schooldimes.payments")
KAMPALA = ZoneInfo("Africa/Kampala")

REFERENCE_PREFIX = {
    Deposit.Purpose.WALLET_TOPUP: "SD-DEP-",
    Deposit.Purpose.GIFT_VOUCHER: "SD-GV-",
    Deposit.Purpose.POOLED_FUND_CONTRIBUTION: "SD-PF-",
}
PAYOUT_PREFIX = "SD-PO-"

ENTRY_TYPE_FOR_PURPOSE = {
    Deposit.Purpose.WALLET_TOPUP: LedgerEntry.EntryType.DEPOSIT,
    Deposit.Purpose.GIFT_VOUCHER: LedgerEntry.EntryType.GIFT_VOUCHER,
    Deposit.Purpose.POOLED_FUND_CONTRIBUTION: LedgerEntry.EntryType.POOLED_FUND_CONTRIBUTION,
}


def new_reference(prefix: str) -> str:
    return f"{prefix}{secrets.token_hex(10).upper()}"


def _validate_channel(channel):
    if channel not in Channel.values:
        raise ServiceError("channel_invalid", _("Unknown payment channel."))


def _student_name(wallet) -> str:
    return wallet.student.name if wallet.student_id else ""


# ---------------------------------------------------------------------------
# Collections (money in)
# ---------------------------------------------------------------------------

def initiate_collection(
    *,
    purpose,
    wallet,
    amount,
    channel,
    payer_phone="",
    idempotency_key,
    initiated_by=None,
    contributor=None,
    recurring_topup=None,
    on_create=None,
):
    """
    Creates a pending Deposit and asks the aggregator to collect. NO money
    moves here. Returns (deposit, created). Retrying with the same
    idempotency_key returns the original deposit (created=False); reusing a
    key for a different request is a 409.
    `on_create(deposit)` runs in the same transaction as the insert (used to
    create the GiftVoucher row atomically with its Deposit).
    """
    amount = validate_amount(amount)
    _validate_channel(channel)
    if not idempotency_key or len(idempotency_key) > 128:
        raise ServiceError("idempotency_key_required", _("An idempotency_key (max 128 chars) is required."))

    def matches(existing):
        return (
            existing.wallet_id == wallet.pk
            and existing.amount == amount
            and existing.purpose == purpose
            and existing.initiated_by_id == getattr(initiated_by, "pk", None)
        )

    existing = Deposit.objects.filter(idempotency_key=idempotency_key).first()
    if existing is not None:
        if not matches(existing):
            raise ServiceError(
                "idempotency_conflict",
                _("This idempotency_key was already used for a different request."),
                status=409,
            )
        return existing, False

    try:
        with transaction.atomic():
            deposit = Deposit.objects.create(
                school_id=wallet.school_id,
                purpose=purpose,
                wallet=wallet,
                amount=amount,
                channel=channel,
                payer_phone=payer_phone or "",
                reference=new_reference(REFERENCE_PREFIX[purpose]),
                initiated_by=initiated_by,
                contributor=contributor,
                recurring_topup=recurring_topup,
                idempotency_key=idempotency_key,
            )
            if on_create:
                on_create(deposit)
    except IntegrityError:
        # a concurrent retry with the same key won the race
        existing = Deposit.objects.filter(idempotency_key=idempotency_key).first()
        if existing is None or not matches(existing):
            raise ServiceError(
                "idempotency_conflict",
                _("This idempotency_key was already used for a different request."),
                status=409,
            )
        return existing, False

    client = get_aggregator_client()
    try:
        result = client.initiate_collection(
            reference=deposit.reference,
            amount=amount,
            channel=channel,
            phone_number=payer_phone,
            description=f"SchoolDimes {purpose}",
        )
    except Exception:
        logger.exception("aggregator initiate_collection failed for %s", deposit.reference)
        _mark_deposit_failed(deposit, "aggregator_error")
        return deposit, True

    deposit.aggregator_ref = result.aggregator_ref or None
    deposit.instructions = result.instructions
    deposit.save(update_fields=["aggregator_ref", "instructions", "updated_at"])
    if result.status == "failed":
        _mark_deposit_failed(deposit, result.failure_reason or "declined")
    return deposit, True


def create_parent_deposit(user, *, wallet, amount, channel, payer_phone, idempotency_key):
    """POST /payments/deposits/ -- a guardian tops up one of their students."""
    if wallet.is_system or not is_guardian(user, wallet.student_id):
        raise ServiceError("not_found", _("Wallet not found."), status=404)
    return initiate_collection(
        purpose=Deposit.Purpose.WALLET_TOPUP,
        wallet=wallet,
        amount=amount,
        channel=channel,
        payer_phone=payer_phone or user.phone_number,
        idempotency_key=idempotency_key,
        initiated_by=user,
    )


def process_payment_event(event: WebhookEvent) -> str:
    """
    THE confirmation path for every aggregator callback (deposits, gift
    vouchers, pooled-fund contributions, payouts), whether it arrives from
    the webhook view, `manage.py mock_webhook`, or mock auto-confirmation.
    Idempotent: a replayed event returns "duplicate" and moves no money.
    Returns one of: confirmed, failed, duplicate, unmatched,
    payout_succeeded, payout_failed.
    """
    reference = event.reference or ""
    if reference.startswith(PAYOUT_PREFIX):
        return _process_payout_event(event)

    deposit = Deposit.objects.filter(reference=reference).first() if reference else None
    if deposit is None and event.aggregator_ref:
        deposit = Deposit.objects.filter(aggregator_ref=event.aggregator_ref).first()
    if deposit is None:
        _unmatched(event, "unknown_reference")
        return "unmatched"

    with transaction.atomic():
        deposit = Deposit.objects.select_for_update().get(pk=deposit.pk)
        if deposit.status == Deposit.Status.CONFIRMED:
            return "duplicate"
        if event.status == "successful":
            if deposit.status == Deposit.Status.FAILED:
                # the aggregator contradicted an earlier failure: a human decides
                _unmatched(event, "late_success_after_failure")
                return "unmatched"
            if event.amount is not None and event.amount != deposit.amount:
                _unmatched(event, "amount_mismatch")
                return "unmatched"
            _confirm_deposit(deposit)
            return "confirmed"
        if deposit.status == Deposit.Status.FAILED:
            return "duplicate"
        _mark_deposit_failed(deposit, event.failure_reason or "declined")
        return "failed"


def _unmatched(event: WebhookEvent, reason: str):
    logger.warning("unmatched webhook %s (%s)", event.reference, reason)
    UnmatchedWebhook.objects.create(
        reference=event.reference[:64],
        aggregator_ref=(event.aggregator_ref or "")[:64],
        reason=reason,
        payload=event.raw,
    )


def _confirm_deposit(deposit: Deposit):
    """Credits the target wallet from the school's aggregator clearing
    wallet. Caller holds the Deposit row lock inside a transaction."""
    clearing = get_system_wallet(deposit.school_id, Wallet.WalletType.AGGREGATOR_CLEARING)
    wallet = deposit.wallet
    post_transfer(
        debit_wallet=clearing,
        credit_wallet=wallet,
        amount=deposit.amount,
        entry_type=ENTRY_TYPE_FOR_PURPOSE[deposit.purpose],
        reference_id=f"deposit:{deposit.pk}",
        description=f"{deposit.get_purpose_display()} {deposit.reference}",
    )
    deposit.status = Deposit.Status.CONFIRMED
    deposit.confirmed_at = timezone.now()
    deposit.failure_reason = ""
    deposit.save(update_fields=["status", "confirmed_at", "failure_reason", "updated_at"])

    payload = {
        "deposit_id": deposit.pk,
        "amount": fmt_amount(deposit.amount),
        "student_name": _student_name(wallet),
        "student_id": wallet.student_id,
    }
    if deposit.purpose == Deposit.Purpose.GIFT_VOUCHER:
        voucher = deposit.gift_voucher
        now = timezone.now()
        voucher.status = GiftVoucher.Status.REDEEMED  # auto-redeem, see DECISIONS.md
        voucher.redeemed_at = now
        voucher.save(update_fields=["status", "redeemed_at"])
        notify_guardians(
            voucher.student,
            "gift_received",
            {**payload, "gift_voucher_id": voucher.pk, "sender_name": voucher.sender_name, "message": voucher.message},
        )
    elif deposit.purpose == Deposit.Purpose.WALLET_TOPUP:
        if deposit.recurring_topup_id:
            rt = deposit.recurring_topup
            rt.consecutive_failures = 0
            rt.last_status = "succeeded"
            rt.save(update_fields=["consecutive_failures", "last_status", "updated_at"])
            notify(rt.parent, "recurring_topup_executed", {**payload, "recurring_topup_id": rt.pk})
        elif deposit.contributor_id:
            notify_guardians(
                wallet.student,
                "contributor_topup_received",
                {**payload, "contributor_name": deposit.contributor.name},
            )
        elif deposit.initiated_by_id:
            notify(deposit.initiated_by, "deposit_confirmed", payload)

    deposit_confirmed.send(sender=Deposit, deposit=deposit)


def _mark_deposit_failed(deposit: Deposit, reason: str, status=Deposit.Status.FAILED):
    deposit.status = status
    deposit.failure_reason = reason[:64]
    deposit.save(update_fields=["status", "failure_reason", "updated_at"])
    payload = {
        "deposit_id": deposit.pk,
        "amount": fmt_amount(deposit.amount),
        "student_name": _student_name(deposit.wallet),
        "student_id": deposit.wallet.student_id,
        "reason": reason,
    }
    if deposit.recurring_topup_id:
        _record_recurring_failure(deposit.recurring_topup, payload)
    elif deposit.initiated_by_id:
        notify(deposit.initiated_by, "deposit_failed", payload)
    if deposit.purpose == Deposit.Purpose.GIFT_VOUCHER:
        GiftVoucher.objects.filter(deposit=deposit).update(status=GiftVoucher.Status.CANCELLED)


def expire_stale_deposits(now=None) -> int:
    """Pending deposits older than DEPOSIT_EXPIRY_HOURS become `expired`.
    A late success webhook still confirms an expired deposit (the payer's
    money was taken), see DECISIONS.md."""
    now = now or timezone.now()
    cutoff = now - timedelta(hours=settings.DEPOSIT_EXPIRY_HOURS)
    count = 0
    for deposit in Deposit.objects.filter(status=Deposit.Status.PENDING, created_at__lt=cutoff):
        with transaction.atomic():
            locked = Deposit.objects.select_for_update().get(pk=deposit.pk)
            if locked.status == Deposit.Status.PENDING:
                _mark_deposit_failed(locked, "expired", status=Deposit.Status.EXPIRED)
                count += 1
    return count


def mock_confirm(deposit: Deposit, *, success=True, failure_reason="declined") -> str:
    """Simulates the aggregator calling our webhook (mock mode only). Goes
    through the exact same process_payment_event() as the real webhook."""
    raw, _headers = MockAggregatorClient.build_webhook(
        reference=deposit.reference,
        aggregator_ref=deposit.aggregator_ref or "",
        amount=deposit.amount,
        success=success,
        failure_reason=failure_reason,
    )
    return process_payment_event(MockAggregatorClient().parse_webhook(raw))


# ---------------------------------------------------------------------------
# Payouts (money out)
# ---------------------------------------------------------------------------

def initiate_payout(*, purpose, source_wallet, amount, phone_number, description="", requested_by=None, idempotency_key=None):
    """
    Debits `source_wallet` into the aggregator clearing wallet NOW (so the
    money can't be spent twice while the payout is in flight), then asks the
    aggregator to pay out. On failure a compensating `reversal` transfer
    puts the money back. Callers must already have authorised the debit.
    """
    amount = validate_amount(amount)
    if not phone_number:
        raise ServiceError("phone_number_required", _("A mobile money phone number is required."))
    if idempotency_key:
        existing = Payout.objects.filter(idempotency_key=idempotency_key).first()
        if existing:
            if existing.source_wallet_id != source_wallet.pk or existing.amount != amount:
                raise ServiceError("idempotency_conflict", _("This idempotency_key was already used for a different request."), status=409)
            return existing

    clearing = get_system_wallet(source_wallet.school_id, Wallet.WalletType.AGGREGATOR_CLEARING)
    with transaction.atomic():
        payout = Payout.objects.create(
            school_id=source_wallet.school_id,
            purpose=purpose,
            source_wallet=source_wallet,
            amount=amount,
            phone_number=phone_number,
            description=description[:255],
            reference=new_reference(PAYOUT_PREFIX),
            requested_by=requested_by,
            idempotency_key=idempotency_key or None,
        )
        post_transfer(
            debit_wallet=source_wallet,
            credit_wallet=clearing,
            amount=amount,
            entry_type=purpose,
            reference_id=f"payout:{payout.pk}",
            description=description[:255] or payout.get_purpose_display(),
        )

    try:
        result = get_aggregator_client().initiate_payout(
            reference=payout.reference, amount=amount, phone_number=phone_number, description=description
        )
    except Exception:
        logger.exception("aggregator initiate_payout failed for %s", payout.reference)
        with transaction.atomic():
            _finish_payout(Payout.objects.select_for_update().get(pk=payout.pk), False, "aggregator_error")
        payout.refresh_from_db()
        return payout

    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(pk=payout.pk)
        payout.aggregator_ref = result.aggregator_ref or None
        payout.save(update_fields=["aggregator_ref"])
        if result.status in ("successful", "failed"):
            _finish_payout(payout, result.status == "successful", result.failure_reason)
    return payout


def _finish_payout(payout: Payout, success: bool, failure_reason=""):
    if payout.status != Payout.Status.PENDING:
        return False
    payout.completed_at = timezone.now()
    if success:
        payout.status = Payout.Status.SUCCEEDED
        payout.save(update_fields=["status", "completed_at"])
    else:
        payout.status = Payout.Status.FAILED
        payout.failure_reason = (failure_reason or "payout_failed")[:64]
        payout.save(update_fields=["status", "failure_reason", "completed_at"])
        clearing = get_system_wallet(payout.school_id, Wallet.WalletType.AGGREGATOR_CLEARING)
        post_transfer(
            debit_wallet=clearing,
            credit_wallet=payout.source_wallet,
            amount=payout.amount,
            entry_type=LedgerEntry.EntryType.REVERSAL,
            reference_id=f"payout:{payout.pk}",
            description=f"Reversal of failed payout {payout.reference}",
        )
    _notify_payout(payout)
    return True


def _notify_payout(payout: Payout):
    if payout.purpose != Payout.Purpose.SAVINGS_WITHDRAWAL:
        return
    wallet = payout.source_wallet
    payload = {
        "payout_id": payout.pk,
        "amount": fmt_amount(payout.amount),
        "student_name": _student_name(wallet),
        "student_id": wallet.student_id,
        "phone_number": payout.phone_number,
        "reason": payout.failure_reason,
    }
    event = "savings_withdrawal_completed" if payout.status == Payout.Status.SUCCEEDED else "savings_withdrawal_failed"
    notify_guardians(wallet.student, event, payload)


def _process_payout_event(event: WebhookEvent) -> str:
    payout = Payout.objects.filter(reference=event.reference).first()
    if payout is None:
        _unmatched(event, "unknown_reference")
        return "unmatched"
    with transaction.atomic():
        payout = Payout.objects.select_for_update().get(pk=payout.pk)
        if not _finish_payout(payout, event.status == "successful", event.failure_reason):
            return "duplicate"
    return "payout_succeeded" if payout.status == Payout.Status.SUCCEEDED else "payout_failed"


# ---------------------------------------------------------------------------
# Contributor top-up links
# ---------------------------------------------------------------------------

def create_topup_link(user, student, expires_at=None) -> StudentTopUpLink:
    if not is_guardian(user, student):
        raise ServiceError("not_found", _("Student not found."), status=404)
    return StudentTopUpLink.objects.create(
        school_id=student.school_id,
        student=student,
        wallet=get_student_wallet(student),
        token=secrets.token_urlsafe(32),
        created_by=user,
        expires_at=expires_at,
    )


def revoke_topup_link(link: StudentTopUpLink) -> StudentTopUpLink:
    link.active = False
    link.revoked_at = timezone.now()
    link.save(update_fields=["active", "revoked_at"])
    return link


def resolve_topup_link(token: str) -> StudentTopUpLink | None:
    """Returns the usable link for `token`, or None (unknown, revoked and
    expired are deliberately indistinguishable to the public caller)."""
    link = (
        StudentTopUpLink.objects.select_related("student", "school", "wallet")
        .filter(token=token, active=True)
        .first()
    )
    if link is None or (link.expires_at and link.expires_at <= timezone.now()):
        return None
    return link


def create_contributor(data: dict) -> Contributor:
    name = (data.get("name") or "").strip()
    if not name:
        raise ServiceError("contributor_name_required", _("Contributor name is required."))
    if not (data.get("phone_number") or data.get("email")):
        raise ServiceError("contributor_contact_required", _("A phone number or email is required."))
    return Contributor.objects.create(
        name=name[:255],
        phone_number=(data.get("phone_number") or "")[:20],
        email=data.get("email") or "",
        relationship_label=(data.get("relationship_label") or "")[:64],
    )


def replayed_public_deposit(link, idempotency_key, purpose):
    """Public retries are answered before a new Contributor row is created."""
    existing = Deposit.objects.filter(idempotency_key=idempotency_key).first()
    if existing is None:
        return None
    if existing.wallet_id != link.wallet_id or existing.purpose != purpose or existing.initiated_by_id:
        raise ServiceError(
            "idempotency_conflict",
            _("This idempotency_key was already used for a different request."),
            status=409,
        )
    return existing


def create_contributor_deposit(link, *, contributor_data, amount, channel, payer_phone, idempotency_key):
    replay = replayed_public_deposit(link, idempotency_key, Deposit.Purpose.WALLET_TOPUP)
    if replay is not None:
        return replay, False
    contributor = create_contributor(contributor_data)
    return initiate_collection(
        purpose=Deposit.Purpose.WALLET_TOPUP,
        wallet=link.wallet,
        amount=amount,
        channel=channel,
        payer_phone=payer_phone or contributor.phone_number,
        idempotency_key=idempotency_key,
        contributor=contributor,
    )


# ---------------------------------------------------------------------------
# Gift vouchers
# ---------------------------------------------------------------------------

def create_gift_voucher(*, student, amount, message, channel, payer_phone, idempotency_key, sender_user=None, sender_contributor=None):
    """Creates a GiftVoucher + its Deposit atomically; money moves (and the
    voucher auto-redeems into the main wallet) only on confirmation."""
    wallet = get_student_wallet(student)
    message = (message or "")[:280]

    def create_voucher(deposit):
        GiftVoucher.objects.create(
            school_id=student.school_id,
            sender_user=sender_user,
            sender_contributor=sender_contributor,
            student=student,
            wallet=wallet,
            amount=deposit.amount,
            message=message,
            deposit=deposit,
        )

    deposit, created = initiate_collection(
        purpose=Deposit.Purpose.GIFT_VOUCHER,
        wallet=wallet,
        amount=amount,
        channel=channel,
        payer_phone=payer_phone,
        idempotency_key=idempotency_key,
        initiated_by=sender_user,
        contributor=sender_contributor,
        on_create=create_voucher,
    )
    return GiftVoucher.objects.get(deposit=deposit), created


# ---------------------------------------------------------------------------
# Recurring top-ups
# ---------------------------------------------------------------------------

def compute_next_run(frequency, day_of_week, day_of_month, after) -> datetime:
    """Next RECURRING_TOPUP_RUN_HOUR:00 Africa/Kampala occurrence strictly
    after `after`, as an aware UTC datetime."""
    local_after = after.astimezone(KAMPALA)
    run_time = time(hour=settings.RECURRING_TOPUP_RUN_HOUR)
    if frequency == RecurringTopUp.Frequency.WEEKLY:
        days_ahead = (day_of_week - local_after.weekday()) % 7
        candidate = datetime.combine(local_after.date() + timedelta(days=days_ahead), run_time, KAMPALA)
        if candidate <= local_after:
            candidate += timedelta(days=7)
    else:
        year, month = local_after.year, local_after.month
        candidate = datetime.combine(local_after.date().replace(day=day_of_month), run_time, KAMPALA)
        if candidate <= local_after:
            month += 1
            if month == 13:
                year, month = year + 1, 1
            candidate = datetime(year, month, day_of_month, run_time.hour, tzinfo=KAMPALA)
    return candidate.astimezone(ZoneInfo("UTC"))


def validate_schedule(frequency, day_of_week, day_of_month):
    if frequency == RecurringTopUp.Frequency.WEEKLY:
        if day_of_week is None or not 0 <= day_of_week <= 6:
            raise ServiceError("schedule_invalid", _("Weekly top-ups need day_of_week between 0 (Monday) and 6 (Sunday)."))
    elif frequency == RecurringTopUp.Frequency.MONTHLY:
        if day_of_month is None or not 1 <= day_of_month <= 28:
            raise ServiceError("schedule_invalid", _("Monthly top-ups need day_of_month between 1 and 28."))
    else:
        raise ServiceError("schedule_invalid", _("frequency must be weekly or monthly."))


def _record_recurring_failure(rt: RecurringTopUp, payload: dict):
    rt.consecutive_failures += 1
    rt.last_status = "failed"
    fields = ["consecutive_failures", "last_status", "updated_at"]
    notify(rt.parent, "recurring_topup_failed", {**payload, "recurring_topup_id": rt.pk})
    if rt.consecutive_failures >= settings.RECURRING_TOPUP_MAX_FAILURES and rt.active:
        rt.active = False
        fields.append("active")
        notify(
            rt.parent,
            "recurring_topup_paused",
            {**payload, "recurring_topup_id": rt.pk, "failures": rt.consecutive_failures},
        )
    rt.save(update_fields=fields)


def run_due_recurring_topups(now=None, *, force=False) -> list[dict]:
    """
    Executes every active RecurringTopUp whose next_run_at has passed (or
    every active one, with force=True). Safe to call concurrently / twice:
    each run window's Deposit uses idempotency_key
    "recurring:<id>:<scheduled next_run_at>", enforced by a DB unique
    constraint, so a double Beat fire can never double top-up.
    Missed windows are not back-filled: next_run_at jumps to the next
    future occurrence.
    """
    now = now or timezone.now()
    qs = RecurringTopUp.objects.filter(active=True)
    if not force:
        qs = qs.filter(next_run_at__lte=now)
    results = []
    client = get_aggregator_client()
    for rt_id in list(qs.values_list("pk", flat=True)):
        with transaction.atomic():
            rt = RecurringTopUp.objects.select_for_update().select_related("parent", "student", "wallet").get(pk=rt_id)
            if not rt.active or (not force and rt.next_run_at > now):
                continue
            scheduled_for = rt.next_run_at
            key = f"recurring:{rt.pk}:{scheduled_for:%Y%m%dT%H%M}"
            already_ran = Deposit.objects.filter(idempotency_key=key).exists()
            rt.next_run_at = compute_next_run(rt.frequency, rt.day_of_week, rt.day_of_month, max(now, scheduled_for))
            rt.last_run_at = now
            rt.save(update_fields=["next_run_at", "last_run_at", "updated_at"])
        if already_ran:
            results.append({"recurring_topup": rt.pk, "outcome": "skipped_duplicate_window"})
            continue
        if not is_guardian(rt.parent, rt.student_id):
            RecurringTopUp.objects.filter(pk=rt.pk).update(active=False, last_status="guardian_unlinked")
            results.append({"recurring_topup": rt.pk, "outcome": "deactivated"})
            continue
        try:
            deposit, created = initiate_collection(
                purpose=Deposit.Purpose.WALLET_TOPUP,
                wallet=rt.wallet,
                amount=rt.amount,
                channel=rt.channel,
                payer_phone=rt.payer_phone,
                idempotency_key=key,
                initiated_by=rt.parent,
                recurring_topup=rt,
            )
        except ServiceError as exc:
            if exc.code == "idempotency_conflict":
                results.append({"recurring_topup": rt.pk, "outcome": "skipped_duplicate_window"})
                continue
            raise
        if not created:
            results.append({"recurring_topup": rt.pk, "outcome": "skipped_duplicate_window"})
            continue
        if deposit.status == Deposit.Status.PENDING:
            RecurringTopUp.objects.filter(pk=rt.pk).update(last_status="pending")
            if client.auto_confirms:
                mock_confirm(deposit)
        deposit.refresh_from_db()
        results.append({"recurring_topup": rt.pk, "outcome": deposit.status, "deposit": deposit.pk})
    return results

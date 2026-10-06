from decimal import Decimal

from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.models import User
from core.audit import audit
from core.exceptions import InsufficientFundsError, ServiceError
from core.money import validate_amount
from core.permissions import is_platform_admin, is_school_admin
from notifications.services import fmt_amount, notify
from payments.models import Deposit, Payout
from payments.services import initiate_collection, initiate_payout
from students.access import user_school_ids
from wallets.models import LedgerEntry, Wallet
from wallets.services import get_system_wallet, post_transfer

from .models import PooledFund, PooledFundContribution, PooledFundDisbursement


def funds_visible_to(user):
    qs = PooledFund.objects.select_related("wallet", "created_by")
    if is_platform_admin(user):
        return qs
    return qs.filter(school_id__in=user_school_ids(user))


def create_fund(user, *, title, purpose="", group_label="", target_amount=None, deadline=None, school_id=None):
    """Parents and school_admins may create funds for a school they belong
    to. A parent with children in several schools must pass `school_id`,
    which is validated against the schools derived from their Guardian links."""
    if user.role not in (User.Role.PARENT, User.Role.SCHOOL_ADMIN):
        raise ServiceError("forbidden", _("Only parents and school admins can create pooled funds."), status=403)
    allowed = user_school_ids(user)
    if school_id is None:
        if len(allowed) != 1:
            raise ServiceError("school_required", _("Choose which school this fund is for."))
        school_id = allowed[0]
    if school_id not in allowed:
        raise ServiceError("not_found", _("School not found."), status=404)
    if target_amount is not None:
        target_amount = validate_amount(target_amount)
    with transaction.atomic():
        wallet = Wallet.objects.create(school_id=school_id, wallet_type=Wallet.WalletType.POOLED_FUND)
        return PooledFund.objects.create(
            school_id=school_id, title=title, purpose=purpose, group_label=group_label,
            created_by=user, target_amount=target_amount, deadline=deadline, wallet=wallet,
        )


def contribute(user, fund, *, amount, channel, payer_phone, idempotency_key):
    if fund.status != PooledFund.Status.OPEN:
        raise ServiceError("fund_not_open", _("This fund is no longer accepting contributions."), status=409)
    if fund.deadline and timezone.localdate() > fund.deadline:
        raise ServiceError("fund_deadline_passed", _("This fund's deadline has passed."), status=409)
    return initiate_collection(
        purpose=Deposit.Purpose.POOLED_FUND_CONTRIBUTION,
        wallet=fund.wallet,
        amount=amount,
        channel=channel,
        payer_phone=payer_phone or user.phone_number,
        idempotency_key=idempotency_key,
        initiated_by=user,
    )


def record_contribution(deposit):
    """deposit_confirmed receiver: log the contribution for a confirmed
    pooled-fund deposit. Money arriving after the fund closed is still
    recorded -- the payer was charged (see DECISIONS.md)."""
    fund = deposit.wallet.pooled_fund
    contribution, created = PooledFundContribution.objects.get_or_create(
        deposit=deposit,
        defaults={
            "fund": fund,
            "contributor_user": deposit.initiated_by,
            "contributor": deposit.contributor,
            "amount": deposit.amount,
        },
    )
    if created and deposit.initiated_by_id:
        notify(deposit.initiated_by, "pooled_fund_contribution_confirmed", {
            "fund_id": fund.pk, "fund_title": fund.title, "amount": fmt_amount(deposit.amount),
        })
    return contribution


def can_close(user, fund) -> bool:
    return fund.created_by_id == user.pk or can_disburse(user, fund)


def can_disburse(user, fund) -> bool:
    return is_platform_admin(user) or (is_school_admin(user) and user.school_id == fund.school_id)


def close_fund(user, fund):
    if not can_close(user, fund):
        raise ServiceError("forbidden", _("Only the fund's creator or a school admin can close it."), status=403)
    if fund.status != PooledFund.Status.OPEN:
        raise ServiceError("fund_not_open", _("This fund is already closed."), status=409)
    fund.status = PooledFund.Status.CLOSED
    fund.closed_at = timezone.now()
    fund.save(update_fields=["status", "closed_at"])
    audit(user, "pooled_fund.close", fund)
    return fund


def disburse(user, fund, *, amount, destination, description, phone_number="", idempotency_key=None):
    """school_admin (or platform_admin) only. Debits the fund wallet into the
    school settlement wallet, or out to a phone via an aggregator payout."""
    if not can_disburse(user, fund):
        raise ServiceError("forbidden", _("Only a school admin can disburse a pooled fund."), status=403)
    amount = validate_amount(amount)
    description = (description or "").strip()
    if not description:
        raise ServiceError("description_required", _("A description of what the money is for is required."))
    if destination not in PooledFundDisbursement.Destination.values:
        raise ServiceError("destination_invalid", _("Unknown disbursement destination."))
    if amount > fund.wallet.cached_balance:
        raise ServiceError("insufficient_funds", _("The fund does not hold that much."), status=422)

    try:
        if destination == PooledFundDisbursement.Destination.EXTERNAL:
            payout = initiate_payout(
                purpose=Payout.Purpose.POOLED_FUND_DISBURSEMENT,
                source_wallet=fund.wallet,
                amount=amount,
                phone_number=phone_number,
                description=description,
                requested_by=user,
                idempotency_key=idempotency_key,
            )
            disbursement = PooledFundDisbursement.objects.create(
                fund=fund, amount=amount, destination=destination,
                description=description[:255], payout=payout, disbursed_by=user,
            )
        else:
            with transaction.atomic():
                disbursement = PooledFundDisbursement.objects.create(
                    fund=fund, amount=amount, destination=destination,
                    description=description[:255], disbursed_by=user,
                )
                post_transfer(
                    debit_wallet=fund.wallet,
                    credit_wallet=get_system_wallet(fund.school_id, Wallet.WalletType.SCHOOL_SETTLEMENT),
                    amount=amount,
                    entry_type=LedgerEntry.EntryType.POOLED_FUND_DISBURSEMENT,
                    reference_id=f"pooled:{fund.pk}:{disbursement.pk}",
                    description=description[:255],
                )
    except InsufficientFundsError:
        raise ServiceError("insufficient_funds", _("The fund does not hold that much."), status=422)

    fund.wallet.refresh_from_db()
    if fund.status == PooledFund.Status.CLOSED and fund.wallet.cached_balance == 0:
        fund.status = PooledFund.Status.DISBURSED
        fund.save(update_fields=["status"])
    audit(user, "pooled_fund.disburse", fund, details={"amount": str(amount), "destination": destination})
    return disbursement


def fund_totals(fund) -> dict:
    """All figures come from the ledger of the fund's wallet."""
    entries = LedgerEntry.objects.filter(wallet=fund.wallet)
    contributed = entries.filter(
        direction=LedgerEntry.Direction.CREDIT, entry_type=LedgerEntry.EntryType.POOLED_FUND_CONTRIBUTION
    ).aggregate(s=Sum("amount"))["s"] or Decimal("0")
    credits = entries.filter(direction=LedgerEntry.Direction.CREDIT).aggregate(s=Sum("amount"))["s"] or Decimal("0")
    debits = entries.filter(direction=LedgerEntry.Direction.DEBIT).aggregate(s=Sum("amount"))["s"] or Decimal("0")
    balance = credits - debits
    progress = None
    if fund.target_amount:
        progress = float(min(Decimal("100"), (contributed / fund.target_amount * 100).quantize(Decimal("0.1"))))
    return {
        "total_contributed": contributed,
        # net of any reversed (failed) external payouts
        "total_disbursed": contributed - balance,
        "balance": balance,
        "progress_percent": progress,
    }



def funds_for(user, params, *, detail=False):
    """GET /pooled-funds/ (?status=); detail prefetches the contribution log."""
    qs = funds_visible_to(user)
    if params.get("status"):
        qs = qs.filter(status=params["status"])
    if detail:
        qs = qs.prefetch_related("contributions__deposit", "contributions__contributor_user",
                                 "contributions__contributor", "disbursements__payout")
    return qs

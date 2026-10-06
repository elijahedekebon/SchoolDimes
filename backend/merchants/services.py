from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.translation import gettext as _

from accounts.models import User
from core.audit import audit
from core.exceptions import ServiceError
from core.permissions import is_platform_admin, is_school_admin
from wallets.models import LedgerEntry, Wallet

from .models import Merchant, MerchantApproval, MerchantStaff


def approved_school_ids(merchant) -> list[int]:
    if merchant is None or merchant.status != Merchant.Status.APPROVED:
        return []
    return list(merchant.approvals.filter(status=MerchantApproval.Status.APPROVED).values_list("school_id", flat=True))


def is_approved_for(merchant, school) -> bool:
    return getattr(school, "pk", school) in approved_school_ids(merchant)


def get_merchant_settlement_wallet(merchant, school_id) -> Wallet:
    """One settlement wallet per (merchant, school): every ledger row stays
    inside one tenant, and a school can reconcile exactly what its students
    paid each merchant."""
    lookup = dict(school_id=school_id, merchant=merchant, wallet_type=Wallet.WalletType.MERCHANT_SETTLEMENT, student=None)
    try:
        with transaction.atomic():
            return Wallet.objects.get_or_create(**lookup)[0]
    except IntegrityError:
        return Wallet.objects.get(**lookup)


def user_merchant(user):
    link = MerchantStaff.objects.filter(user=user).select_related("merchant").first()
    return link.merchant if link else None


def create_merchant(user, *, name, category="", contact_phone=""):
    """A school_admin registers a nearby merchant; it is approved for their
    school straight away. platform_admin creates it unattached."""
    if not (is_school_admin(user) or is_platform_admin(user)):
        raise ServiceError("forbidden", _("Only school or platform admins can add merchants."), status=403)
    with transaction.atomic():
        merchant = Merchant.objects.create(name=name, category=category, contact_phone=contact_phone, created_by=user)
        if is_school_admin(user):
            set_approval(user, merchant, MerchantApproval.Status.APPROVED)
    audit(user, "merchant.create", merchant)
    return merchant


def set_approval(user, merchant, status, school_id=None):
    """school_admin approves/suspends a merchant for THEIR OWN school only."""
    if is_platform_admin(user):
        if school_id is None:
            raise ServiceError("school_required", _("platform_admin must pass school."))
    elif is_school_admin(user):
        school_id = user.school_id
    else:
        raise ServiceError("forbidden", _("Only a school admin can approve merchants."), status=403)
    approval, _created = MerchantApproval.objects.get_or_create(merchant=merchant, school_id=school_id)
    approval.status = status
    approval.decided_by = user
    approval.decided_at = timezone.now()
    approval.save()
    if status == MerchantApproval.Status.APPROVED:
        get_merchant_settlement_wallet(merchant, school_id)
    audit(user, f"merchant.{status}", merchant, school_id=school_id)
    return approval


def link_staff(actor, merchant, staff_user):
    if staff_user.role != User.Role.MERCHANT_STAFF:
        raise ServiceError("role_invalid", _("Only merchant_staff users can be linked to a merchant."))
    if not (is_platform_admin(actor) or (is_school_admin(actor) and is_approved_for(merchant, actor.school_id))):
        raise ServiceError("forbidden", _("You cannot manage this merchant's staff."), status=403)
    link, _created = MerchantStaff.objects.update_or_create(user=staff_user, defaults={"merchant": merchant})
    audit(actor, "merchant.link_staff", merchant, details={"user": staff_user.pk})
    return link


def statement(merchant, *, school_ids, date_from=None, date_to=None):
    """Ledger lines on the merchant's settlement wallets (sales credited,
    refunds/recoveries), restricted to `school_ids`."""
    wallets = Wallet.objects.filter(
        merchant=merchant, wallet_type=Wallet.WalletType.MERCHANT_SETTLEMENT, school_id__in=school_ids
    )
    entries = LedgerEntry.objects.filter(wallet__in=wallets).select_related("wallet").order_by("-created_at", "-id")
    if date_from:
        entries = entries.filter(created_at__gte=date_from)
    if date_to:
        entries = entries.filter(created_at__lt=date_to)
    return wallets, entries



def merchants_for(user, params=None):
    """school_admin/platform_admin: every merchant (to find and approve ones a
    neighbouring school registered); parents: merchants approved for their
    children's schools; merchant_staff: their own."""
    from accounts.models import User
    from core.permissions import is_platform_admin, is_school_admin
    from students.access import user_school_ids

    from .models import Merchant, MerchantApproval

    qs = Merchant.objects.prefetch_related("approvals")
    if is_platform_admin(user) or is_school_admin(user):
        return qs
    if user.role == User.Role.PARENT:
        return qs.filter(approvals__school_id__in=user_school_ids(user),
                         approvals__status=MerchantApproval.Status.APPROVED, status=Merchant.Status.APPROVED).distinct()
    if user.role == User.Role.MERCHANT_STAFF:
        return qs.filter(staff__user=user)
    return qs.none()



def merchant_statement(user, merchant, params):
    """GET /merchants/{id}/statement/: merchant_staff of this merchant (all its
    schools, ?school= to narrow) and school_admin (their own school only).
    ?from=&to= (Kampala days). Returns wallets, the entries queryset and totals."""
    from datetime import datetime, time, timedelta
    from decimal import Decimal

    from django.db.models import Sum
    from django.utils.dateparse import parse_date
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError
    from core.permissions import is_platform_admin, is_school_admin
    from policies.services import KAMPALA

    if is_platform_admin(user) or user_merchant(user) == merchant:
        school_ids = approved_school_ids(merchant) or list(merchant.approvals.values_list("school_id", flat=True))
        if params.get("school"):
            school_ids = [int(params["school"])] if int(params["school"]) in school_ids else []
    elif is_school_admin(user):
        school_ids = [user.school_id]
    else:
        raise ServiceError("not_found", _("Merchant not found."), status=404)

    def day(key, plus=0):
        value = params.get(key)
        parsed = parse_date(value) if value else None
        if value and parsed is None:
            raise ServiceError("date_invalid", _("Dates must be YYYY-MM-DD."))
        return datetime.combine(parsed + timedelta(days=plus), time.min, KAMPALA) if parsed else None

    wallets, entries = statement(merchant, school_ids=school_ids, date_from=day("from"), date_to=day("to", plus=1))
    credits = entries.filter(direction="credit").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    debits = entries.filter(direction="debit").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    return {"merchant": merchant, "school_ids": school_ids, "wallets": wallets, "entries": entries,
            "total_credits": credits, "total_debits": debits}

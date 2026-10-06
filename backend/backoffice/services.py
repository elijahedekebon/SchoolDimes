"""Part 4A platform back-office services (platform_admin)."""
from datetime import timedelta
from decimal import Decimal

from django.db import transaction
from django.db.models import Count, Q, Sum
from django.utils import timezone

from accounts.models import User
from accounts.services import create_staff_user
from core.audit import audit
from policies.services import get_school_policy
from tenants.models import School
from tenants.services import get_school_settings
from wallets.models import Wallet
from wallets.services import get_system_wallet

POLICY_FIELDS = ("daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap",
                 "p2p_enabled", "low_balance_threshold")
SETTINGS_FIELDS = ("offline_spend_ceiling", "pin_lockout_threshold", "device_stale_after_hours",
                   "attendance_notify_guardians", "attendance_on_canteen_devices")


@transaction.atomic
def onboard_school(actor, *, name, address="", branding=None, supported_languages=None,
                   policy=None, settings=None, admin):
    """Creates a ready-to-use school in one transaction: the School, its
    settings, its default spending policy, its two system wallets
    (school_settlement, aggregator_clearing) and its first school_admin.
    Nothing else is needed before the admin can register devices, add
    students, issue cards and take sales."""
    school = School.objects.create(
        name=name, address=address, branding=branding or {},
        supported_languages=supported_languages or ["en"],
    )
    school_settings = get_school_settings(school)
    for f, v in (settings or {}).items():
        if f in SETTINGS_FIELDS:
            setattr(school_settings, f, v)
    school_settings.save()
    default_policy = get_school_policy(school)
    for f, v in (policy or {}).items():
        if f in POLICY_FIELDS:
            setattr(default_policy, f, v)
    default_policy.updated_by = actor
    default_policy.save()
    get_system_wallet(school, Wallet.WalletType.SCHOOL_SETTLEMENT)
    get_system_wallet(school, Wallet.WalletType.AGGREGATOR_CLEARING)
    first_admin = create_staff_user(
        actor, email=admin["email"], password=admin["password"], role="school_admin",
        full_name=admin.get("full_name", ""), phone_number=admin.get("phone_number", ""),
        school_id=school.pk, preferred_language=admin.get("preferred_language", "en"),
    )
    audit(actor, "school.onboard", school, school_id=school.pk, details={"admin": first_admin.email}, force=True)
    return school, first_admin


def school_stats():
    """One row per school with the numbers support needs at a glance.
    Money comes from the cached wallet balances (== the ledger, enforced by
    post_ledger_entry) and the POS rows the ledger references."""
    from cards.models import Card
    from pos.models import Device, PosTransaction

    since = timezone.now() - timedelta(days=30)
    schools = School.objects.annotate(
        n_students=Count("students", distinct=True),
        n_admins=Count("users", filter=Q(users__role=User.Role.SCHOOL_ADMIN, users__is_active=True), distinct=True),
    ).order_by("name")
    cards = dict(Card.objects.filter(status="active").values_list("school").annotate(n=Count("id")))
    devices = dict(Device.objects.filter(status="active").values_list("school").annotate(n=Count("id")))
    balances = dict(Wallet.objects.filter(wallet_type__in=["main", "savings"]).values_list("school")
                    .annotate(t=Sum("cached_balance")))
    sales = {r["school"]: r for r in PosTransaction.objects.filter(received_at__gte=since)
             .exclude(sync_status="rejected").values("school").annotate(n=Count("id"), t=Sum("applied_amount"))}
    out = []
    for s in schools:
        sale = sales.get(s.pk, {})
        out.append({
            "id": s.pk, "name": s.name, "branding": s.branding, "supported_languages": s.supported_languages,
            "created_at": s.created_at, "students": s.n_students, "school_admins": s.n_admins,
            "active_cards": cards.get(s.pk, 0), "active_devices": devices.get(s.pk, 0),
            "student_balances_total": str(balances.get(s.pk) or Decimal("0.00")),
            "sales_30d_count": sale.get("n", 0), "sales_30d_collected": str(sale.get("t") or Decimal("0.00")),
        })
    return out



def audit_logs_for(user, params):
    """GET /audit-logs/ (platform_admin): ?school=, ?action= (contains), ?actor=."""
    from core.models import AuditLog
    from core.permissions import is_platform_admin

    qs = AuditLog.objects.select_related("actor", "school").order_by("-created_at", "-id")
    if not is_platform_admin(user):
        return qs.none()
    if params.get("school"):
        qs = qs.filter(school_id=params["school"])
    if params.get("action"):
        qs = qs.filter(action__icontains=params["action"])
    if params.get("actor"):
        qs = qs.filter(actor_id=params["actor"])
    return qs


def unmatched_webhooks_for(user, params):
    """Webhooks that matched no payment (no school, so platform_admin only). ?reviewed="""
    from core.permissions import is_platform_admin
    from payments.models import UnmatchedWebhook

    qs = UnmatchedWebhook.objects.all() if is_platform_admin(user) else UnmatchedWebhook.objects.none()
    if params.get("reviewed") in ("true", "false"):
        qs = qs.filter(reviewed=params["reviewed"] == "true")
    return qs


def mark_webhook_reviewed(actor, hook):
    """Records that someone looked into it. No money moves."""
    hook.reviewed = True
    hook.save(update_fields=["reviewed"])
    audit(actor, "unmatched_webhook.reviewed", hook, force=True)
    return hook

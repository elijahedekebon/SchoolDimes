"""
POS business logic (Section D): device registry, offline cache, batch sync,
online purchase, PIN lockout and shortfall review/recovery. Merchant devices
(Section G) use exactly the same functions; scope and settlement wallet are
chosen by device_scope_school_ids() / credit_wallet_for().
"""
import logging
import secrets
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import IntegrityError, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _

from cards.models import Card
from cards.services import freeze_card, verify_pin
from core.audit import audit
from core.exceptions import LedgerError, ServiceError
from core.money import validate_amount
from notifications.services import fmt_amount, notify_guardians, notify_school_admins
from policies.models import Policy, Product, ProductCategory
from policies.services import get_school_policy, kampala_day_bounds, purchases_between, resolve
from tenants.services import get_school_settings
from wallets.models import LedgerEntry, Wallet
from wallets.services import (
    DebitContext,
    DebitKind,
    debit_violations,
    get_student_wallet,
    get_system_wallet,
    post_transfer,
    require_debit,
)

from .authentication import hash_token
from .models import Device, PinFailureReport, PosTransaction, PosTransactionItem

logger = logging.getLogger("schooldimes.pos")
MAX_BATCH = 500
FLAG_ONLY = {"insufficient_funds"}  # handled as shortfall, not as a flag


# ---------------------------------------------------------------------------
# Devices
# ---------------------------------------------------------------------------

def _new_token():
    raw = secrets.token_urlsafe(32)
    return raw, hash_token(raw), raw[:8]


def register_device(actor, *, school, device_name, device_role, merchant=None):
    """Returns (device, raw_token). The raw token is shown exactly once."""
    if device_role not in Device.Role.values:
        raise ServiceError("device_role_invalid", _("Unknown device role."))
    _check_merchant_for_role(school, device_role, merchant)
    raw, token_hash, prefix = _new_token()
    fields = dict(school=school, device_name=device_name, device_role=device_role,
                  token_hash=token_hash, token_prefix=prefix, registered_by=actor)
    if merchant is not None:
        fields["merchant"] = merchant
    device = Device.objects.create(**fields)
    audit(actor, "device.register", device)
    return device, raw


def _check_merchant_for_role(school, device_role, merchant):
    if device_role == Device.Role.MERCHANT:
        if not hasattr(Device, "merchant"):
            raise ServiceError("merchant_required", _("Merchant devices need a merchant."))
        from merchants.services import is_approved_for

        if merchant is None or not is_approved_for(merchant, school):
            raise ServiceError("merchant_not_approved", _("That merchant is not approved for this school."))
    elif merchant is not None:
        raise ServiceError("merchant_not_allowed", _("Only merchant devices have a merchant."))


def revoke_device(actor, device):
    device.status = Device.Status.REVOKED
    device.revoked_at = timezone.now()
    device.save(update_fields=["status", "revoked_at"])
    audit(actor, "device.revoke", device)
    return device


def rotate_device_token(actor, device):
    if device.status != Device.Status.ACTIVE:
        raise ServiceError("device_revoked", _("A revoked device cannot get a new token."), status=409)
    raw, token_hash, prefix = _new_token()
    device.token_hash, device.token_prefix = token_hash, prefix
    device.save(update_fields=["token_hash", "token_prefix"])
    audit(actor, "device.rotate_token", device)
    return device, raw


def stale_devices(school_id, now=None):
    now = now or timezone.now()
    hours = get_school_settings(school_id).device_stale_after_hours
    cutoff = now - timedelta(hours=hours)
    return Device.objects.filter(school_id=school_id, status=Device.Status.ACTIVE).filter(
        Q(last_sync_at__lt=cutoff) | Q(last_sync_at__isnull=True, created_at__lt=cutoff)
    )


# ---------------------------------------------------------------------------
# Scope
# ---------------------------------------------------------------------------

def device_merchant_id(device):
    return getattr(device, "merchant_id", None)


def device_scope_school_ids(device) -> list[int]:
    """Schools whose cards this device may see and charge. Canteen and
    attendance devices: their own school. Merchant devices: every school that
    has approved the device's merchant (Section G)."""
    if device.device_role == Device.Role.MERCHANT and device_merchant_id(device):
        from merchants.services import approved_school_ids

        return approved_school_ids(device.merchant)
    return [device.school_id]


def credit_wallet_for(device, school_id) -> Wallet:
    """Where a sale's money goes: the school's settlement wallet for canteen
    sales, the merchant's per-school settlement wallet for merchant sales."""
    if device.device_role == Device.Role.MERCHANT and device_merchant_id(device):
        from merchants.services import get_merchant_settlement_wallet

        return get_merchant_settlement_wallet(device.merchant, school_id)
    return get_system_wallet(school_id, Wallet.WalletType.SCHOOL_SETTLEMENT)


def _products_for(device):
    qs = Product.objects.filter(school_id__in=device_scope_school_ids(device)).select_related("category")
    merchant_id = device_merchant_id(device)
    if device.device_role == Device.Role.MERCHANT:
        qs = qs.filter(merchant_id=merchant_id)
    elif hasattr(Product, "merchant"):
        qs = qs.filter(merchant__isnull=True)
    return qs


# ---------------------------------------------------------------------------
# Offline cache
# ---------------------------------------------------------------------------

def money(value) -> str:
    return str(Decimal(value or 0).quantize(Decimal("0.01")))


def pin_hash_scheme() -> dict:
    from django.contrib.auth.hashers import get_hasher

    return {
        "format": "<algorithm>$<iterations>$<salt>$<hash>",
        "algorithm": get_hasher().algorithm,  # "pbkdf2_sha256" in every non-test environment
        "verify": "base64(PBKDF2-HMAC-SHA256(password=utf8(pin), salt=utf8(salt), iterations, dklen=32)) == hash",
        "note": "Django's default hasher; iterations are per-hash (read them from the string).",
    }


def build_cache(device, since=None, now=None) -> dict:
    """GET /pos/cache/ payload. With `since`, only rows changed after it are
    returned (cards whose card/wallet/student/override changed; products and
    categories changed). A change to a school's default policy or settings
    forces every card of that school to be re-sent."""
    school_ids = device_scope_school_ids(device)
    # created lazily -- do it BEFORE taking the timestamp, so their creation
    # never looks like a change on the next ?since= refresh
    school_policies = {sid: get_school_policy(sid) for sid in school_ids}
    school_settings = {sid: get_school_settings(sid) for sid in school_ids}
    # `now` is taken before reading any rows, so anything that changes while
    # the cache is being built is re-sent on the next ?since=<generated_at>.
    now = now or timezone.now()
    day_start, day_end = kampala_day_bounds(now)
    full_school_ids = set(school_ids) if since is None else {
        sid for sid in school_ids
        if school_policies[sid].updated_at > since or school_settings[sid].updated_at > since
    }

    cards = Card.objects.filter(school_id__in=school_ids).select_related("student", "student__school")
    if since is not None:
        cards = cards.filter(
            Q(school_id__in=full_school_ids)
            | Q(updated_at__gt=since)
            | Q(student__updated_at__gt=since)
            | Q(student__wallets__wallet_type="main", student__wallets__updated_at__gt=since)
            | Q(student__policy_override__updated_at__gt=since)
        ).distinct()
    cards = list(cards)

    student_ids = {c.student_id for c in cards}
    wallets = {w.student_id: w for w in Wallet.objects.filter(student_id__in=student_ids, wallet_type="main")}
    for sid in student_ids - set(wallets):
        student = next(c.student for c in cards if c.student_id == sid)
        wallets[sid] = get_student_wallet(student)
    spend = dict(
        PosTransaction.objects.filter(
            wallet__in=wallets.values(), sync_status__in=["applied", "shortfall"],
            device_local_timestamp__gte=day_start, device_local_timestamp__lt=day_end,
        ).order_by().values_list("wallet_id").annotate(s=Sum("amount"))
    )
    overrides = {p.student_id: p for p in Policy.objects.filter(student_id__in=student_ids)}
    policy_cache = {}

    card_rows = []
    for card in cards:
        student = card.student
        wallet = wallets[student.pk]
        if student.pk not in policy_cache:
            policy_cache[student.pk] = resolve(school_policies[student.school_id], overrides.get(student.pk)).to_dict()
        card_rows.append({
            "card_id": card.pk,
            "card_uid": card.card_uid,
            "status": card.status,
            "pin_hash": card.pin_hash,
            "student_id": student.pk,
            "student_display_name": student.name,
            "photo_url": student.photo.url if student.photo else None,
            "school_id": student.school_id,
            "wallet_id": wallet.pk,
            "balance": str(wallet.cached_balance),
            "today_spend": money(spend.get(wallet.pk)),
            "offline_spend_ceiling": money(school_settings[student.school_id].offline_spend_ceiling),
            "policy": policy_cache[student.pk],
        })

    products = _products_for(device)
    categories = ProductCategory.objects.filter(school_id__in=school_ids)
    if since is not None:
        products = products.filter(Q(updated_at__gt=since) | Q(category__updated_at__gt=since))
        categories = categories.filter(updated_at__gt=since)

    return {
        "generated_at": now.isoformat(),
        "cache_version": int(now.timestamp() * 1000),
        "since": since.isoformat() if since else None,
        "full": since is None,
        "full_school_ids": sorted(full_school_ids),
        "spend_day": day_start.date().isoformat(),
        "device": {
            "id": device.pk, "device_name": device.device_name, "device_role": device.device_role,
            "school_id": device.school_id, "merchant_id": device_merchant_id(device),
        },
        "school_ids": school_ids,
        "offline_spend_ceilings": {str(sid): money(s.offline_spend_ceiling) for sid, s in school_settings.items()},
        "pin_lockout_threshold": {str(sid): s.pin_lockout_threshold for sid, s in school_settings.items()},
        "pin_hash_scheme": pin_hash_scheme(),
        "cards": card_rows,
        "products": [
            {"id": p.pk, "name": p.name, "category_id": p.category_id, "category_name": p.category.name,
             "price": str(p.price), "active": p.active and p.category.active, "school_id": p.school_id,
             "merchant_id": getattr(p, "merchant_id", None)}
            for p in products
        ],
        "categories": [
            {"id": c.pk, "name": c.name, "is_unhealthy": c.is_unhealthy, "active": c.active, "school_id": c.school_id}
            for c in categories
        ],
    }


# ---------------------------------------------------------------------------
# Sync
# ---------------------------------------------------------------------------

def _parse_ts(value):
    if not value:
        return None
    ts = parse_datetime(str(value))
    if ts is not None and timezone.is_naive(ts):
        ts = timezone.make_aware(ts, timezone.get_default_timezone())
    return ts


def _result(txn: PosTransaction, status=None):
    return {
        "idempotency_key": txn.idempotency_key,
        "status": status or txn.sync_status,
        "transaction_id": txn.pk,
        "amount": str(txn.amount),
        "applied_amount": str(txn.applied_amount),
        "shortfall_amount": str(txn.shortfall_amount),
        "flags": txn.flags,
        "reason": txn.reject_reason or None,
    }


def _prepare_items(device, raw_items, amount):
    """Validates line items against the device's scope. Returns
    (items, error_code). Sum of line totals must equal the sale amount."""
    items, total = [], Decimal("0")
    scope = device_scope_school_ids(device)
    for raw in raw_items or []:
        try:
            qty = int(raw.get("quantity", 1))
            unit = Decimal(str(raw.get("unit_price")))
        except Exception:
            return None, "items_invalid"
        if qty < 1 or unit < 0:
            return None, "items_invalid"
        product = None
        if raw.get("product_id"):
            product = Product.objects.filter(pk=raw["product_id"], school_id__in=scope).select_related("category").first()
            if product is None:
                return None, "unknown_product"
        category = product.category if product else None
        if category is None and raw.get("category_id"):
            category = ProductCategory.objects.filter(pk=raw["category_id"], school_id__in=scope).first()
        line_total = (unit * qty).quantize(Decimal("0.01"))
        total += line_total
        items.append({
            "product": product, "category": category, "quantity": qty, "unit_price": unit, "line_total": line_total,
            "description": (raw.get("description") or (product.name if product else "Item"))[:255],
        })
    if items and total != amount:
        return None, "amount_mismatch"
    return items, None


def _store_rejected(device, raw, reason, card=None, amount=None):
    txn = PosTransaction.objects.create(
        device=device,
        merchant_id=device_merchant_id(device),
        school_id=card.school_id if card else device.school_id,
        card=card,
        card_uid=str(raw.get("card_uid", ""))[:64],
        student=card.student if card else None,
        amount=amount if amount is not None else Decimal("0"),
        idempotency_key=str(raw["idempotency_key"])[:128],
        device_local_timestamp=_parse_ts(raw.get("device_local_timestamp")),
        sync_status=PosTransaction.SyncStatus.REJECTED,
        reject_reason=reason,
    )
    return _result(txn)


def _existing(device, key):
    return PosTransaction.objects.filter(device=device, idempotency_key=key).first()


def record_sale(device, raw: dict, *, channel=PosTransaction.Channel.OFFLINE_SYNC, pin=None) -> dict:
    """
    Records one sale. Idempotent per (device, idempotency_key) via a DB
    unique constraint: a replay returns the original result with status
    "duplicate" and moves no money.

    OFFLINE (channel=offline_sync) -- the documented exception to the debit
    gate: the sale already happened, so it is always recorded. The wallet is
    debited up to its true balance; any remainder is a `shortfall`, and any
    broken card/policy rule is a `flag`; both go to admin review.
    ONLINE (channel=online) -- authorize_debit() is enforced in real time
    and a refusal raises DebitRefused (nothing is recorded).
    """
    key = str(raw.get("idempotency_key") or "")[:128]
    if not key:
        return {"idempotency_key": None, "status": "rejected", "reason": "idempotency_key_required"}
    existing = _existing(device, key)
    if existing:
        return _result(existing, "duplicate")

    scope = device_scope_school_ids(device)
    card = Card.objects.select_related("student").filter(card_uid=str(raw.get("card_uid", "")), school_id__in=scope).first()
    try:
        amount = validate_amount(raw.get("amount"))
    except ServiceError as exc:
        return _stored_or_duplicate(lambda: _store_rejected(device, raw, exc.code, card), device, key)
    if card is None:
        return _stored_or_duplicate(lambda: _store_rejected(device, raw, "unknown_card", None, amount), device, key)
    ts = _parse_ts(raw.get("device_local_timestamp"))
    if channel == PosTransaction.Channel.OFFLINE_SYNC and ts is None:
        return _stored_or_duplicate(lambda: _store_rejected(device, raw, "timestamp_required", card, amount), device, key)
    items, error = _prepare_items(device, raw.get("items"), amount)
    if error:
        return _stored_or_duplicate(lambda: _store_rejected(device, raw, error, card, amount), device, key)

    pin_verified = raw.get("pin_verified")
    if channel == PosTransaction.Channel.ONLINE and pin is not None:
        if not verify_pin(card, str(pin)):
            report_pin_failures(device, card, 1, timezone.now())
            raise ServiceError("pin_invalid", _("Wrong PIN."), status=422)
        pin_verified = True

    wallet = get_student_wallet(card.student)
    merchant_id = device_merchant_id(device)
    context = DebitContext(
        kind=DebitKind.PURCHASE, card=card, merchant_id=merchant_id,
        items=[{"product_id": i["product"].pk if i["product"] else None,
                "category_id": i["category"].pk if i["category"] else None} for i in items],
        now=min(ts, timezone.now()) if ts else None,
    )
    try:
        with transaction.atomic():
            if channel == PosTransaction.Channel.ONLINE:
                require_debit(wallet, amount, context)
                flags = []
            else:
                locked = Wallet.objects.select_for_update(of=("self",)).select_related("student").get(pk=wallet.pk)
                flags = [v for v in debit_violations(locked, amount, context, check_balance=False) if v not in FLAG_ONLY]
            txn = PosTransaction.objects.create(
                device=device, merchant_id=merchant_id, school_id=card.school_id, card=card, card_uid=card.card_uid,
                student=card.student, wallet=wallet, channel=channel, amount=amount,
                idempotency_key=key, device_local_timestamp=ts or timezone.now(),
                sync_status=PosTransaction.SyncStatus.APPLIED, flags=flags,
                pin_verified=pin_verified if isinstance(pin_verified, bool) else None,
            )
            for item in items:
                PosTransactionItem.objects.create(transaction=txn, **item)
            wallet.refresh_from_db()
            applied = min(amount, max(wallet.cached_balance, Decimal("0")))
            reference = f"pos:{txn.pk}"
            if applied > 0:
                post_transfer(
                    debit_wallet=wallet,
                    credit_wallet=credit_wallet_for(device, card.school_id),
                    amount=applied,
                    entry_type=LedgerEntry.EntryType.POS_PURCHASE,
                    reference_id=reference,
                    description=f"{device.device_name}: " + ", ".join(i["description"] for i in items)[:200],
                )
            shortfall = amount - applied
            if shortfall > 0 and shortfall > get_school_settings(card.school_id).offline_spend_ceiling:
                flags.append("exceeds_offline_ceiling")
            txn.applied_amount = applied
            txn.shortfall_amount = shortfall
            txn.flags = flags
            txn.ledger_reference = reference if applied > 0 else ""
            if shortfall > 0:
                txn.sync_status = PosTransaction.SyncStatus.SHORTFALL
            if shortfall > 0 or flags:
                txn.review_status = PosTransaction.ReviewStatus.PENDING
            txn.save()
            _notify_review(txn)
    except IntegrityError:
        existing = _existing(device, key)
        if existing:
            return _result(existing, "duplicate")
        raise
    return _result(txn)


def _stored_or_duplicate(store, device, key):
    try:
        with transaction.atomic():
            return store()
    except IntegrityError:
        return _result(_existing(device, key), "duplicate")


def _notify_review(txn):
    if txn.review_status != PosTransaction.ReviewStatus.PENDING:
        return
    payload = {
        "pos_transaction_id": txn.pk, "student_id": txn.student_id, "student_name": txn.student.name,
        "device_name": txn.device.device_name, "shortfall_amount": fmt_amount(txn.shortfall_amount),
        "flags": txn.flags,
    }
    if txn.shortfall_amount > 0:
        notify_school_admins(txn.school_id, "shortfall_flagged", payload)
    else:
        notify_school_admins(txn.school_id, "pos_transaction_flagged", payload)


def sync_batch(device, transactions: list, pin_failures: list | None = None) -> dict:
    """POST /pos/sync/. Applies transactions in device-timestamp order; one
    bad transaction never fails the batch. Returns per-transaction results and
    refreshed authoritative balances for every card involved."""
    if len(transactions) > MAX_BATCH:
        raise ServiceError("batch_too_large", _("At most %(n)s transactions per sync.") % {"n": MAX_BATCH})
    results, card_uids = [], set()

    def sort_key(raw):
        ts = _parse_ts(raw.get("device_local_timestamp")) if isinstance(raw, dict) else None
        return (ts is None, ts or timezone.now())

    for raw in sorted([t for t in transactions if isinstance(t, dict)], key=sort_key):
        card_uids.add(str(raw.get("card_uid", "")))
        try:
            results.append(record_sale(device, raw))
        except (ServiceError, LedgerError) as exc:
            results.append({"idempotency_key": raw.get("idempotency_key"), "status": "rejected",
                            "reason": getattr(exc, "code", "ledger_error")})
        except Exception:  # never fail the whole batch
            logger.exception("POS sync failed for %s", raw.get("idempotency_key"))
            results.append({"idempotency_key": raw.get("idempotency_key"), "status": "rejected", "reason": "internal_error"})
    for bad in [t for t in transactions if not isinstance(t, dict)]:
        results.append({"idempotency_key": None, "status": "rejected", "reason": "malformed"})

    for report in pin_failures or []:
        try:
            card = Card.objects.filter(card_uid=str(report.get("card_uid", "")),
                                       school_id__in=device_scope_school_ids(device)).first()
            if card:
                card_uids.add(card.card_uid)
                report_pin_failures(device, card, int(report.get("failed_attempts", 1)),
                                    _parse_ts(report.get("device_local_timestamp")))
        except Exception:
            logger.exception("bad pin failure report")

    Device.objects.filter(pk=device.pk).update(last_sync_at=timezone.now())
    return {"results": results, "balances": card_balances(device, card_uids), "server_time": timezone.now().isoformat()}


def card_balances(device, card_uids) -> list:
    day_start, day_end = kampala_day_bounds()
    rows = []
    for card in Card.objects.filter(card_uid__in=card_uids, school_id__in=device_scope_school_ids(device)).select_related("student"):
        wallet = get_student_wallet(card.student)
        today = purchases_between(wallet, day_start, day_end)
        rows.append({"card_uid": card.card_uid, "card_status": card.status, "wallet_id": wallet.pk,
                     "balance": money(wallet.cached_balance), "today_spend": money(today)})
    return rows


# ---------------------------------------------------------------------------
# PIN lockout
# ---------------------------------------------------------------------------

def report_pin_failures(device, card, failed_attempts, device_local_timestamp=None):
    """Records wrong-PIN attempts; freezes the card once the school's
    pin_lockout_threshold is reached within 24 hours."""
    failed_attempts = max(1, min(int(failed_attempts), 50))
    PinFailureReport.objects.create(device=device, card=card, failed_attempts=failed_attempts,
                                    device_local_timestamp=device_local_timestamp)
    since = timezone.now() - timedelta(hours=24)
    total = PinFailureReport.objects.filter(card=card, received_at__gte=since).aggregate(s=Sum("failed_attempts"))["s"] or 0
    threshold = get_school_settings(card.school_id).pin_lockout_threshold
    if total >= threshold and card.status == Card.Status.ACTIVE:
        freeze_card(card)
        notify_guardians(card.student, "card_locked_pin_failures", {
            "card_id": card.pk, "student_id": card.student_id, "student_name": card.student.name, "failures": total,
        })
        return True
    return False


# ---------------------------------------------------------------------------
# Shortfall / flag review
# ---------------------------------------------------------------------------

def resolve_review(actor, txn: PosTransaction, resolution: str, notes=""):
    """
    accept                  -- flagged sale (no shortfall) acknowledged. No ledger effect.
    write_off               -- the school/merchant absorbs the shortfall. No ledger
                               entry: the missing money never existed in any wallet.
    recover_from_next_topup -- collect the shortfall from the student's main wallet
                               now (whatever is there) and from every future confirmed
                               deposit until repaid: main -> settlement,
                               entry_type shortfall_recovery, ref recovery:<txn>:<n>.
    charge_guardian         -- as recover_from_next_topup, plus a collection request
                               (Deposit) for the shortfall to the primary guardian's phone.
    """
    if txn.review_status != PosTransaction.ReviewStatus.PENDING:
        raise ServiceError("not_pending", _("This transaction is not awaiting review."), status=409)
    if resolution not in PosTransaction.Resolution.values:
        raise ServiceError("resolution_invalid", _("Unknown resolution."))
    if resolution == PosTransaction.Resolution.ACCEPT and txn.shortfall_amount > 0:
        raise ServiceError("resolution_invalid", _("A shortfall must be written off or recovered."))
    if resolution != PosTransaction.Resolution.ACCEPT and txn.shortfall_amount == 0:
        raise ServiceError("resolution_invalid", _("There is no shortfall to recover or write off."))

    txn.resolution = resolution
    txn.reviewed_by, txn.reviewed_at, txn.review_notes = actor, timezone.now(), notes
    if resolution in (PosTransaction.Resolution.ACCEPT, PosTransaction.Resolution.WRITE_OFF):
        txn.review_status = PosTransaction.ReviewStatus.RESOLVED
        txn.save()
    else:
        txn.review_status = PosTransaction.ReviewStatus.RECOVERY_PENDING
        txn.save()
        recover_shortfalls(txn.wallet)
        if resolution == PosTransaction.Resolution.CHARGE_GUARDIAN:
            _charge_guardian(txn)
    audit(actor, f"pos.review.{resolution}", txn)
    txn.refresh_from_db()
    return txn


def _charge_guardian(txn):
    from payments.models import Deposit
    from payments.services import initiate_collection
    from students.models import Guardian

    txn.refresh_from_db()
    outstanding = txn.shortfall_amount - txn.recovered_amount
    link = (Guardian.objects.filter(student=txn.student).select_related("parent")
            .order_by("-is_primary_contact", "created_at").first())
    if outstanding <= 0 or link is None:
        return None
    deposit, _created = initiate_collection(
        purpose=Deposit.Purpose.WALLET_TOPUP, wallet=txn.wallet, amount=outstanding, channel="momo",
        payer_phone=link.parent.phone_number, idempotency_key=f"shortfall:{txn.pk}", initiated_by=link.parent,
    )
    return deposit


def recover_shortfalls(wallet) -> Decimal:
    """Collects outstanding recover-pending shortfalls (oldest first) from
    the wallet's current balance. Called on review and on every confirmed
    deposit into the wallet. This is an admin-approved debt collection, not
    spending, so it is not subject to authorize_debit (see DECISIONS.md)."""
    if wallet is None:
        return Decimal("0")
    collected = Decimal("0")
    pending = PosTransaction.objects.filter(
        wallet=wallet, review_status=PosTransaction.ReviewStatus.RECOVERY_PENDING
    ).select_related("device").order_by("received_at", "id")
    for txn in pending:
        with transaction.atomic():
            locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)
            txn = PosTransaction.objects.select_for_update().get(pk=txn.pk)
            outstanding = txn.shortfall_amount - txn.recovered_amount
            take = min(outstanding, locked_wallet.cached_balance)
            if take <= 0:
                break
            n = LedgerEntry.objects.filter(reference_id__startswith=f"recovery:{txn.pk}:").count() // 2 + 1
            post_transfer(
                debit_wallet=locked_wallet,
                credit_wallet=credit_wallet_for(txn.device, txn.school_id),
                amount=take,
                entry_type=LedgerEntry.EntryType.SHORTFALL_RECOVERY,
                reference_id=f"recovery:{txn.pk}:{n}",
                description=f"Recovery of POS shortfall #{txn.pk}",
            )
            txn.recovered_amount += take
            if txn.recovered_amount >= txn.shortfall_amount:
                txn.review_status = PosTransaction.ReviewStatus.RESOLVED
            txn.save(update_fields=["recovered_amount", "review_status"])
            collected += take
    return collected


# ---------------------------------------------------------------------------
# P2P at the POS (card + PIN)
# ---------------------------------------------------------------------------

def pos_p2p_transfer(device, *, sender_card_uid, pin, recipient_card_uid, amount, idempotency_key, note=""):
    from wallets.p2p import p2p_transfer

    scope = [device.school_id]  # P2P is canteen-device only, same school
    sender_card = Card.objects.select_related("student").filter(card_uid=sender_card_uid, school_id__in=scope).first()
    recipient_card = Card.objects.select_related("student").filter(card_uid=recipient_card_uid, school_id__in=scope).first()
    if sender_card is None or recipient_card is None:
        raise ServiceError("unknown_card", _("Unknown card."), status=404)
    if not verify_pin(sender_card, str(pin)):
        report_pin_failures(device, sender_card, 1, timezone.now())
        raise ServiceError("pin_invalid", _("Wrong PIN."), status=422)
    if recipient_card.status != Card.Status.ACTIVE:
        raise ServiceError("recipient_card_inactive", _("The recipient's card is not active."), status=422)
    return p2p_transfer(sender_card.student, recipient_card.student, amount, device=device,
                        sender_card=sender_card, note=note, idempotency_key=idempotency_key)

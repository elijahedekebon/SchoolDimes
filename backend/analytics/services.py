"""
Read-only analytics & reconciliation (Section K). Everything is computed
from existing rows (PosTransaction/Item, LedgerEntry, Deposit, FeePayment,
PooledFund...); nothing new is stored. Day/hour bucketing is Africa/Kampala.
Money figures: `gross` = amount rung up at the till, `collected` = what the
ledger actually moved (applied_amount); the difference is the shortfall.
"""
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.db.models import Count, F, Q, Sum
from django.db.models.functions import ExtractHour, TruncDate
from django.utils import timezone

from fees.models import FeePayment
from payments.models import Deposit
from policies.services import KAMPALA
from pooled_funds.models import PooledFund
from pos.models import Device, PosTransaction, PosTransactionItem
from pos.services import money, stale_devices
from wallets.models import LedgerEntry, Wallet

COUNTED = [PosTransaction.SyncStatus.APPLIED, PosTransaction.SyncStatus.SHORTFALL]


def day_bounds(day_from: date, day_to: date):
    start = datetime.combine(day_from, time.min, KAMPALA)
    end = datetime.combine(day_to + timedelta(days=1), time.min, KAMPALA)
    return start, end


def default_range():
    today = timezone.now().astimezone(KAMPALA).date()
    return today - timedelta(days=29), today


def _sales(school_ids, start, end):
    return PosTransaction.objects.filter(
        school_id__in=school_ids, sync_status__in=COUNTED,
        device_local_timestamp__gte=start, device_local_timestamp__lt=end,
    )


def _totals(qs):
    agg = qs.aggregate(n=Count("id"), gross=Sum("amount"), collected=Sum("applied_amount"), short=Sum("shortfall_amount"))
    return {"transactions": agg["n"], "gross_amount": money(agg["gross"]),
            "collected_amount": money(agg["collected"]), "shortfall_amount": money(agg["short"])}


def _rows(qs, keys):
    rows = qs.values(*keys).annotate(n=Count("id"), gross=Sum("amount"), collected=Sum("applied_amount")).order_by(*keys)
    return [{**{k: r[k] for k in keys}, "transactions": r["n"], "gross_amount": money(r["gross"]),
             "collected_amount": money(r["collected"])} for r in rows]


def sales_summary(school_ids, day_from, day_to, *, per_school=False):
    start, end = day_bounds(day_from, day_to)
    qs = _sales(school_ids, start, end)
    by_day = _rows(qs.annotate(date=TruncDate("device_local_timestamp", tzinfo=KAMPALA)), ["date"])
    for r in by_day:
        r["date"] = r["date"].isoformat()
    by_device = _rows(qs.annotate(device_name=F("device__device_name")), ["device_id", "device_name"])
    by_merchant = _rows(qs.annotate(merchant_name=F("merchant__name")), ["merchant_id", "merchant_name"])
    for r in by_merchant:
        r["merchant_name"] = r["merchant_name"] or "School canteen"
    result = {"from": day_from.isoformat(), "to": day_to.isoformat(), "totals": _totals(qs),
              "by_day": by_day, "by_device": by_device, "by_merchant": by_merchant}
    if per_school:
        result["by_school"] = _rows(qs.annotate(school_name=F("school__name")), ["school_id", "school_name"])
    return result


def _items(school_ids, start, end):
    return PosTransactionItem.objects.filter(
        transaction__school_id__in=school_ids, transaction__sync_status__in=COUNTED,
        transaction__device_local_timestamp__gte=start, transaction__device_local_timestamp__lt=end,
    )


def best_sellers(school_ids, day_from, day_to, limit=10):
    start, end = day_bounds(day_from, day_to)
    rows = (_items(school_ids, start, end)
            .values("product_id", "description")
            .annotate(quantity=Sum("quantity"), revenue=Sum("line_total"), transactions=Count("transaction", distinct=True))
            .order_by("-quantity", "-revenue")[:limit])
    return {"from": day_from.isoformat(), "to": day_to.isoformat(), "results": [
        {"product_id": r["product_id"], "name": r["description"], "quantity": r["quantity"],
         "revenue": money(r["revenue"]), "transactions": r["transactions"]} for r in rows]}


def peak_hours(school_ids, day_from, day_to):
    start, end = day_bounds(day_from, day_to)
    rows = {r["hour"]: r for r in _sales(school_ids, start, end)
            .annotate(hour=ExtractHour("device_local_timestamp", tzinfo=KAMPALA))
            .values("hour").annotate(n=Count("id"), gross=Sum("amount"))}
    return {"from": day_from.isoformat(), "to": day_to.isoformat(), "timezone": "Africa/Kampala", "results": [
        {"hour": h, "transactions": rows[h]["n"] if h in rows else 0,
         "gross_amount": money(rows[h]["gross"] if h in rows else 0)} for h in range(24)]}


def category_breakdown(school_ids, day_from, day_to):
    start, end = day_bounds(day_from, day_to)
    rows = list(_items(school_ids, start, end)
                .values("category_id", "category__name", "category__is_unhealthy")
                .annotate(quantity=Sum("quantity"), revenue=Sum("line_total")).order_by("-revenue"))
    total = sum((r["revenue"] or Decimal("0")) for r in rows)
    unhealthy = sum((r["revenue"] or Decimal("0")) for r in rows if r["category__is_unhealthy"])
    pct = lambda v: float(round(Decimal(v) / total * 100, 1)) if total else 0.0  # noqa: E731
    return {
        "from": day_from.isoformat(), "to": day_to.isoformat(),
        "total_item_revenue": money(total),
        "unhealthy_revenue": money(unhealthy),
        "unhealthy_share_percent": pct(unhealthy),
        "results": [{"category_id": r["category_id"], "name": r["category__name"] or "Uncategorized",
                     "is_unhealthy": bool(r["category__is_unhealthy"]), "quantity": r["quantity"],
                     "revenue": money(r["revenue"]), "share_percent": pct(r["revenue"] or 0)} for r in rows],
    }


def student_spending(student, day_from, day_to):
    start, end = day_bounds(day_from, day_to)
    wallets = Wallet.objects.filter(student=student)
    entries = LedgerEntry.objects.filter(wallet__in=wallets, created_at__gte=start, created_at__lt=end)

    def total(**f):
        return money(entries.filter(**f).aggregate(s=Sum("amount"))["s"])

    by_day = (entries.filter(direction="debit", entry_type="pos_purchase")
              .annotate(date=TruncDate("created_at", tzinfo=KAMPALA)).values("date")
              .annotate(spent=Sum("amount")).order_by("date"))
    items = PosTransactionItem.objects.filter(
        transaction__student=student, transaction__sync_status__in=COUNTED,
        transaction__device_local_timestamp__gte=start, transaction__device_local_timestamp__lt=end)
    categories = (items.values("category__name", "category__is_unhealthy")
                  .annotate(quantity=Sum("quantity"), revenue=Sum("line_total")).order_by("-revenue"))
    top = items.values("description").annotate(quantity=Sum("quantity"), revenue=Sum("line_total")).order_by("-quantity")[:5]
    return {
        "student": student.pk, "from": day_from.isoformat(), "to": day_to.isoformat(),
        "purchases_total": total(direction="debit", entry_type="pos_purchase"),
        "fees_total": total(direction="debit", entry_type="fee_payment"),
        "p2p_sent_total": total(direction="debit", entry_type="p2p_transfer_out"),
        "p2p_received_total": total(direction="credit", entry_type="p2p_transfer_in"),
        "topups_total": total(direction="credit", entry_type__in=["deposit", "gift_voucher"]),
        "refunds_total": total(direction="credit", entry_type="refund"),
        "by_day": [{"date": r["date"].isoformat(), "spent": money(r["spent"])} for r in by_day],
        "by_category": [{"name": r["category__name"] or "Uncategorized", "is_unhealthy": bool(r["category__is_unhealthy"]),
                         "quantity": r["quantity"], "revenue": money(r["revenue"])} for r in categories],
        "top_items": [{"name": r["description"], "quantity": r["quantity"], "revenue": money(r["revenue"])} for r in top],
    }


def reconciliation(school_id, day: date):
    """One school, one Kampala day. Each POS/fee figure is cross-checked
    against the ledger rows that carry its reference_id; `matches` is false
    if they disagree (it never should)."""
    start, end = day_bounds(day, day)
    devices = []
    for device in Device.objects.filter(Q(school_id=school_id) | Q(transactions__school_id=school_id)).distinct():
        txns = PosTransaction.objects.filter(device=device, school_id=school_id, received_at__gte=start, received_at__lt=end,
                                             sync_status__in=COUNTED)
        collected = txns.aggregate(s=Sum("applied_amount"))["s"] or Decimal("0")
        refs = [f"pos:{pk}" for pk in txns.values_list("pk", flat=True)]
        ledger = LedgerEntry.objects.filter(school_id=school_id, reference_id__in=refs, direction="debit",
                                            entry_type="pos_purchase").aggregate(s=Sum("amount"))["s"] or Decimal("0")
        devices.append({
            "device_id": device.pk, "device_name": device.device_name, "device_role": device.device_role,
            "status": device.status, "last_sync_at": device.last_sync_at.isoformat() if device.last_sync_at else None,
            "transactions": txns.count(), "rejected": PosTransaction.objects.filter(
                device=device, school_id=school_id, received_at__gte=start, received_at__lt=end,
                sync_status=PosTransaction.SyncStatus.REJECTED).count(),
            "collected_amount": money(collected), "ledger_amount": money(ledger), "matches": collected == ledger,
        })
    open_reviews = PosTransaction.objects.filter(school_id=school_id, review_status__in=["pending", "recovery_pending"])
    outstanding = sum((t.shortfall_amount - t.recovered_amount for t in open_reviews if t.resolution != "write_off"), Decimal("0"))

    deposits_confirmed = Deposit.objects.filter(school_id=school_id, status="confirmed", confirmed_at__gte=start, confirmed_at__lt=end)
    dep_refs = [f"deposit:{pk}" for pk in deposits_confirmed.values_list("pk", flat=True)]
    dep_ledger = LedgerEntry.objects.filter(school_id=school_id, reference_id__in=dep_refs, direction="credit").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    dep_total = deposits_confirmed.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    fees = FeePayment.objects.filter(school_id=school_id, created_at__gte=start, created_at__lt=end)
    fee_total = fees.aggregate(s=Sum("amount"))["s"] or Decimal("0")
    fee_ledger = LedgerEntry.objects.filter(school_id=school_id, reference_id__in=list(fees.values_list("ledger_reference", flat=True)),
                                            direction="debit").aggregate(s=Sum("amount"))["s"] or Decimal("0")
    system = {w.wallet_type: money(w.cached_balance) for w in Wallet.objects.filter(
        school_id=school_id, wallet_type__in=["school_settlement", "aggregator_clearing"])}
    books_total = Wallet.objects.filter(school_id=school_id).aggregate(s=Sum("cached_balance"))["s"] or Decimal("0")
    return {
        "school": school_id, "date": day.isoformat(), "timezone": "Africa/Kampala",
        "devices": devices,
        "stale_devices": [{"device_id": d.pk, "device_name": d.device_name,
                           "last_sync_at": d.last_sync_at.isoformat() if d.last_sync_at else None}
                          for d in stale_devices(school_id)],
        "unresolved_reviews": {"count": open_reviews.count(), "outstanding_shortfall": money(outstanding)},
        "deposits": {
            "confirmed_count": deposits_confirmed.count(), "confirmed_amount": money(dep_total),
            "ledger_amount": money(dep_ledger), "matches": dep_total == dep_ledger,
            "pending_count": Deposit.objects.filter(school_id=school_id, status="pending").count(),
            "pending_amount": money(Deposit.objects.filter(school_id=school_id, status="pending").aggregate(s=Sum("amount"))["s"]),
        },
        "fee_payments": {"count": fees.count(), "amount": money(fee_total), "ledger_amount": money(fee_ledger),
                         "matches": fee_total == fee_ledger},
        "pooled_funds": [{"fund_id": f.pk, "title": f.title, "status": f.status, "balance": money(f.wallet.cached_balance)}
                         for f in PooledFund.objects.filter(school_id=school_id).select_related("wallet")],
        "system_wallets": system,
        "books_total": money(books_total),
        "books_balanced": books_total == 0,
    }

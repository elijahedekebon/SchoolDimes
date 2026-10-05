"""Part 4A: a student's itemized money history (parent app + admin).

One row per ledger entry on the student's main/savings wallets, enriched
with the POS sale behind it (device, merchant, line items, flags) and with
whether -- and how -- it can be disputed.
"""
from datetime import date

from django.utils.translation import gettext as _

from core.exceptions import ServiceError
from wallets.models import LedgerEntry

# Debits a guardian may dispute, and how (see the disputes API).
_POS_TYPES = {"pos_purchase"}
_LEDGER_DISPUTABLE = {"fee_payment", "shortfall_recovery"}


def history_queryset(student, params):
    """?wallet=main|savings, ?entry_type=, ?direction=credit|debit,
    ?from=YYYY-MM-DD&to=YYYY-MM-DD (inclusive Africa/Kampala days)."""
    from analytics.services import day_bounds

    qs = LedgerEntry.objects.filter(wallet__student=student, wallet__wallet_type__in=["main", "savings"]) \
        .select_related("wallet").order_by("-created_at", "-id")
    if params.get("wallet") in ("main", "savings"):
        qs = qs.filter(wallet__wallet_type=params["wallet"])
    if params.get("entry_type"):
        qs = qs.filter(entry_type__in=params["entry_type"].split(","))
    if params.get("direction") in ("credit", "debit"):
        qs = qs.filter(direction=params["direction"])
    if params.get("from") or params.get("to"):
        try:
            d_from = date.fromisoformat(params.get("from") or "2000-01-01")
            d_to = date.fromisoformat(params.get("to") or "2999-12-31")
        except ValueError:
            raise ServiceError("date_invalid", _("Dates must be YYYY-MM-DD."))
        start, end = day_bounds(d_from, d_to)
        qs = qs.filter(created_at__gte=start, created_at__lt=end)
    return qs


def _pos_id(entry):
    kind, _sep, rest = entry.reference_id.partition(":")
    if kind in ("pos", "recovery") and rest:
        try:
            return int(rest.split(":")[0])
        except ValueError:
            return None
    return None


def serialize_history(entries):
    """Serializes ledger entries with their POS sale and dispute info, in 3
    queries regardless of page size."""
    from disputes.models import Dispute
    from pos.models import PosTransaction

    entries = list(entries)
    pos_ids = {i for i in (_pos_id(e) for e in entries) if i}
    sales = {
        t.pk: t for t in PosTransaction.objects.filter(pk__in=pos_ids)
        .select_related("device", "merchant").prefetch_related("items")
    }
    open_disputes = {}
    for d in Dispute.objects.filter(status__in=["open", "under_review"]).filter(
            pos_transaction_id__in=pos_ids).values("id", "pos_transaction_id"):
        open_disputes[("pos", d["pos_transaction_id"])] = d["id"]
    for d in Dispute.objects.filter(status__in=["open", "under_review"],
                                    ledger_entry_id__in=[e.pk for e in entries]).values("id", "ledger_entry_id"):
        open_disputes[("entry", d["ledger_entry_id"])] = d["id"]

    rows = []
    for e in entries:
        sale = sales.get(_pos_id(e)) if e.entry_type in ("pos_purchase", "shortfall_recovery", "refund") else None
        if e.direction == "debit" and e.entry_type in _POS_TYPES and sale:
            target = {"pos_transaction": sale.pk}
            open_id = open_disputes.get(("pos", sale.pk))
        elif e.direction == "debit" and e.entry_type in _LEDGER_DISPUTABLE:
            target = {"ledger_entry": e.pk}
            open_id = open_disputes.get(("entry", e.pk))
        else:
            target, open_id = None, None
        rows.append({
            "id": e.pk,
            "wallet": e.wallet_id,
            "wallet_type": e.wallet.wallet_type,
            "direction": e.direction,
            "amount": str(e.amount),
            "entry_type": e.entry_type,
            "reference_id": e.reference_id,
            "description": e.description,
            "created_at": e.created_at,
            "pos": None if sale is None else {
                "transaction_id": sale.pk,
                "device_name": sale.device.device_name,
                "merchant_id": sale.merchant_id,
                "merchant_name": sale.merchant.name if sale.merchant else None,
                "sale_time": sale.device_local_timestamp,
                "sync_status": sale.sync_status,
                "flags": sale.flags,
                "amount": str(sale.amount),
                "items": [{"product": i.product_id, "description": i.description, "category": i.category_id,
                           "quantity": i.quantity, "unit_price": str(i.unit_price), "line_total": str(i.line_total)}
                          for i in sale.items.all()],
            },
            "dispute_target": target,
            "open_dispute": open_id,
        })
    return rows

"""School admin pages (was src/app/school/**). Views only gather data from
the services and render; every queryset goes through web.core.scoping."""
from django.shortcuts import render
from django.utils.translation import gettext as _

from analytics import services as analytics
from pos import services as pos_services
from pos.serializers import PosTransactionSerializer, ResolveSerializer
from web.core.csv import csv_response
from web.core.dates import kampala_today, shift_day, valid_day
from web.core.mixins import ActionView, PageView
from web.core.money import shillings
from web.core.paging import paginate

# ---------------------------------------------------------------------------
# Section B -- overview, sales, reconciliation, review queue
# ---------------------------------------------------------------------------


class OverviewView(PageView):
    """/school: today's numbers, each linking to the page that explains it."""

    template_name = "school/index.html"
    regions = {"overview": ("school/_overview.html", "overview")}

    def overview(self):
        user = self.request.user
        today = kampala_today()
        day = analytics.parse_day(today, "date")
        school_ids, _cross = analytics.school_scope(user, {})
        return {
            "today": today,
            "sales": analytics.sales_summary(school_ids, day, day),
            "recon": analytics.reconciliation(school_ids[0], day),
            "reviews": self.scoped("shortfalls").count(),
            "disputes": self.scoped("disputes", {"status": "open"}).count(),
            "alerts": self.scoped("p2p_alerts", {"status": "open"}).count(),
            "stale": len(self.scoped("devices", {"stale": "true"})),
            "requests": self.scoped("data_requests", {"status": "pending"}).count(),
        }


def _range(params, default_days):
    today = kampala_today()
    return {"from": valid_day(params.get("from"), shift_day(today, -default_days)),
            "to": valid_day(params.get("to"), today)}


class SalesView(PageView):
    """/school/sales: summary for a date range + all transactions (filters)."""

    template_name = "school/sales/index.html"
    regions = {
        "sales_summary": ("school/sales/_summary.html", "summary"),
        "transactions_table": ("school/sales/_transactions.html", "transactions"),
    }

    def page_context(self):
        devices = self.scoped("devices", {"page_size": 100}).order_by("device_name")[:100]
        return {"range": _range(self.params, 6),
                "device_options": [(d.pk, d.device_name) for d in devices],
                "sync_options": [(v, v) for v in ("applied", "shortfall", "rejected")]}

    def summary(self):
        rng = _range(self.params, 6)
        school_ids, _cross = analytics.school_scope(self.request.user, {})
        s = analytics.sales_summary(school_ids, *analytics.date_range(rng))
        chart = {"type": "bar", "labels": [r["date"] for r in s["by_day"]],
                 "values": [shillings(r["collected_amount"]) for r in s["by_day"]], "money": True}
        return {"summary": s, "chart": chart}

    def transactions(self):
        filters = {k: self.params.get(k, "") for k in ("device", "sync_status")}
        page = paginate(self.scoped("transactions", filters), self.params)
        return {"page": page, "rows": PosTransactionSerializer(page.object_list, many=True).data, "filters": filters}


class TransactionDrawerView(PageView):
    """Per-transaction detail with line items (was TransactionDrawer)."""

    def get(self, request, pk):
        txn = self.scoped_object("transactions", pk)
        return render(request, "school/sales/_transaction_drawer.html", {"t": PosTransactionSerializer(txn).data})


def _recon_day(params):
    return valid_day(params.get("date"), kampala_today())


class ReconciliationView(PageView):
    template_name = "school/reconciliation/index.html"
    regions = {"recon": ("school/reconciliation/_recon.html", "recon")}

    def page_context(self):
        return {"date": _recon_day(self.params)}

    def recon(self):
        school_ids, _cross = analytics.school_scope(self.request.user, {})
        return {"data": analytics.reconciliation(school_ids[0], analytics.parse_day(_recon_day(self.params), "date"))}


class ReconciliationExportView(PageView):
    """Same rows and columns the browser-side CSV had."""

    def get(self, request):
        school_ids, _cross = analytics.school_scope(request.user, {})
        data = analytics.reconciliation(school_ids[0], analytics.parse_day(_recon_day(request.GET), "date"))
        rows = [
            *({"section": "device", "name": d["device_name"], "role": d["device_role"], "count": d["transactions"],
               "rejected": d["rejected"], "amount": d["collected_amount"], "ledger_amount": d["ledger_amount"],
               "matches": d["matches"], "last_sync_at": d["last_sync_at"]} for d in data["devices"]),
            {"section": "deposits_confirmed", "count": data["deposits"]["confirmed_count"],
             "amount": data["deposits"]["confirmed_amount"], "ledger_amount": data["deposits"]["ledger_amount"],
             "matches": data["deposits"]["matches"]},
            {"section": "deposits_pending", "count": data["deposits"]["pending_count"],
             "amount": data["deposits"]["pending_amount"]},
            {"section": "fee_payments", "count": data["fee_payments"]["count"], "amount": data["fee_payments"]["amount"],
             "ledger_amount": data["fee_payments"]["ledger_amount"], "matches": data["fee_payments"]["matches"]},
            {"section": "unresolved_reviews", "count": data["unresolved_reviews"]["count"],
             "amount": data["unresolved_reviews"]["outstanding_shortfall"]},
            *({"section": "pooled_fund", "name": f["title"], "role": f["status"], "amount": f["balance"]}
              for f in data["pooled_funds"]),
            *({"section": "system_wallet", "name": k, "amount": v} for k, v in data["system_wallets"].items()),
            *({"section": "stale_device", "name": d["device_name"], "last_sync_at": d["last_sync_at"]}
              for d in data["stale_devices"]),
            {"section": "books_total", "amount": data["books_total"], "matches": data["books_balanced"]},
        ]
        return csv_response(f"reconciliation-{data['date']}.csv", rows,
                            ["section", "name", "role", "count", "rejected", "amount", "ledger_amount", "matches",
                             "last_sync_at"])


class ShortfallsView(PageView):
    template_name = "school/shortfalls/index.html"
    regions = {"review_table": ("school/shortfalls/_table.html", "table")}

    def page_context(self):
        return {"type_options": [("shortfall", _("Shortfalls")), ("flagged", _("Policy flags only"))],
                "review_options": [("recovery_pending", "recovery pending"), ("resolved", "resolved")]}

    def table(self):
        filters = {k: self.params.get(k, "") for k in ("type", "review_status")}
        page = paginate(self.scoped("shortfalls", filters), self.params)
        return {"page": page, "rows": PosTransactionSerializer(page.object_list, many=True).data, "filters": filters}


RESOLUTION_LABELS = {
    "recover_from_next_topup": (_("Recover from next top-up"),
                                _("Takes what the student's main wallet holds now, then collects from every later "
                                  "confirmed top-up until the shortfall is repaid.")),
    "charge_guardian": (_("Charge the guardian"),
                        _("Same as recovery, plus a payment request for the outstanding amount is sent to the "
                          "primary guardian's phone.")),
    "write_off": (_("Write off"), _("No money moves. The school (or merchant) absorbs the outstanding amount.")),
    "accept": (_("Accept (acknowledge the flag)"),
               _("No money moves. The flag is acknowledged and the sale stays as recorded.")),
}


class ResolveReviewView(ActionView):
    """POST /school/shortfalls/<id>/resolve (was ResolveButton)."""

    template_name = "school/shortfalls/_resolve.html"

    def setup_object(self):
        self.txn = self.scoped_object("review_items", self.kwargs["pk"])

    def dialog_context(self):
        t = PosTransactionSerializer(self.txn).data
        has_shortfall = t["shortfall_amount"] != "0.00"
        options = ["recover_from_next_topup", "charge_guardian", "write_off"] if has_shortfall else ["accept"]
        return {"t": t, "has_shortfall": has_shortfall,
                "options": [(o, *RESOLUTION_LABELS[o]) for o in options]}

    def perform(self, data):
        s = ResolveSerializer(data={"resolution": data.get("resolution"), "review_notes": data.get("review_notes", "")})
        s.is_valid(raise_exception=True)
        return pos_services.resolve_review(self.request.user, self.txn, s.validated_data["resolution"],
                                           s.validated_data.get("review_notes", ""))


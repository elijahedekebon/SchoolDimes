"""Section B: overview, sales (+drawer), reconciliation (+CSV), review queue."""
import pytest

from pos.models import PosTransaction

from .conftest import hx

pytestmark = pytest.mark.django_db


def test_overview_counts_link_to_their_pages(admin_a_web, pos_a):
    body = admin_a_web.get("/school").content.decode()
    assert "Sales today (collected)" in body and "UGX 10,000" in body  # 3,000 + 7,000 collected
    for href in ("/school/sales", "/school/reconciliation", "/school/shortfalls", "/school/disputes",
                 "/school/p2p-alerts", "/school/devices", "/school/privacy"):
        assert f'href="{href}"' in body
    assert "Balanced" in body


def test_sales_page_summary_chart_and_transactions(admin_a_web, pos_a, pos_b):
    body = admin_a_web.get("/school/sales").content.decode()
    assert 'id="sales-chart"' in body and "Canteen 1" in body
    assert "B till" not in body  # school B's device/sales never appear
    region = admin_a_web.get("/school/sales", {"sync_status": "shortfall"}, **hx("transactions_table")).content.decode()
    assert region.startswith('<div id="transactions_table"') and f"<td>{pos_a['shortfall_id']}</td>" in region
    assert f"<td>{pos_a['sale_id']}</td>" not in region


def test_transaction_drawer_shows_line_items_and_is_tenant_scoped(admin_a_web, pos_a, pos_b):
    body = admin_a_web.get(f"/school/sales/transactions/{pos_a['sale_id']}", **hx()).content.decode()
    assert "Rice" in body and "UGX 3,000" in body
    assert admin_a_web.get(f"/school/sales/transactions/{pos_b['shortfall_id']}", **hx()).status_code == 404


def test_reconciliation_and_csv(admin_a_web, pos_a):
    body = admin_a_web.get("/school/reconciliation").content.decode()
    assert "Books balanced" in body and "Canteen 1" in body and "matches ledger" in body
    r = admin_a_web.get("/school/reconciliation/export")
    assert r["Content-Type"].startswith("text/csv")
    lines = r.content.decode().splitlines()
    assert lines[0] == "section,name,role,count,rejected,amount,ledger_amount,matches,last_sync_at"
    assert any(line.startswith("device,Canteen 1,canteen,2,0,10000.00,10000.00,true") for line in lines)
    assert lines[-1].startswith("books_total,,,,,0.00,,true")


def test_review_queue_resolve_and_isolation(admin_a_web, admin_b_web, pos_a, pos_b):
    body = admin_a_web.get("/school/shortfalls").content.decode()
    assert f"#{pos_a['shortfall_id']}" in body and f"#{pos_b['shortfall_id']}" not in body
    dialog = admin_a_web.get(f"/school/shortfalls/{pos_a['shortfall_id']}/resolve", **hx()).content.decode()
    assert "Recover from next top-up" in dialog and "Write off" in dialog
    r = admin_a_web.post(f"/school/shortfalls/{pos_a['shortfall_id']}/resolve",
                         {"resolution": "write_off", "review_notes": "ok"}, **hx())
    assert "sd-close" in r["HX-Trigger"]
    txn = PosTransaction.objects.get(pk=pos_a["shortfall_id"])
    assert txn.review_status == "resolved" and txn.resolution == "write_off"
    # school B's admin can't see or resolve school A's item
    assert admin_b_web.get(f"/school/shortfalls/{pos_a['shortfall_id']}/resolve", **hx()).status_code == 404
    assert admin_b_web.post(f"/school/shortfalls/{pos_b['shortfall_id']}/resolve",
                            {"resolution": "bogus"}, **hx()).status_code == 200  # dialog with the error
    assert PosTransaction.objects.get(pk=pos_b["shortfall_id"]).review_status == "pending"


def test_resolve_error_is_shown_in_the_dialog(admin_a_web, pos_a):
    body = admin_a_web.post(f"/school/shortfalls/{pos_a['shortfall_id']}/resolve", {"resolution": "accept"},
                            **hx()).content.decode()
    assert 'data-testid="error-alert"' in body

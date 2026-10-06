"""Web migration, Section J: every endpoint docs/PARENT_APP_READINESS.md lists
(copied here: the backend container doesn't mount docs/) still resolves after
the API views were refactored onto shared services."""
import pytest
from django.urls import Resolver404, resolve

# (method, path) for every row of the PARENT_APP_READINESS.md screen table.
PARENT_ENDPOINTS = [
    ("POST", "auth/register"), ("POST", "auth/login"), ("POST", "auth/refresh"), ("POST", "auth/logout"),
    ("GET", "guardian-verifications/"), ("GET", "parent/dashboard/"), ("GET", "financial-literacy-tips/"),
    ("GET", "students/1/"), ("GET", "students/1/transactions/"), ("GET", "analytics/students/1/spending/"),
    ("POST", "payments/deposits/"), ("GET", "payments/deposits/1/"), ("GET", "payments/recurring-topups/"),
    ("PATCH", "payments/recurring-topups/1/"), ("POST", "payments/gift-vouchers/"), ("POST", "payments/topup-links/"),
    ("POST", "payments/topup-links/1/revoke/"), ("GET", "pooled-funds/"), ("GET", "pooled-funds/1/"),
    ("POST", "pooled-funds/1/contribute/"), ("GET", "students/1/spending-controls/"), ("POST", "policies/"),
    ("PATCH", "policies/1/"), ("GET", "product-categories/"), ("GET", "products/"), ("GET", "merchants/"),
    ("POST", "wallets/1/savings/move-in/"), ("POST", "wallets/1/savings/move-out/"), ("GET", "savings-goals/"),
    ("PUT", "wallets/1/savings/withdrawal-window/"), ("POST", "wallets/1/savings/withdraw/"),
    ("GET", "payments/payouts/"), ("GET", "cards/"), ("POST", "cards/1/freeze/"), ("POST", "cards/1/unfreeze/"),
    ("POST", "cards/1/report-lost/"), ("GET", "students/1/p2p-history/"), ("POST", "wallets/transfer/"),
    ("POST", "disputes/"), ("GET", "notifications/"), ("POST", "notifications/1/read/"),
    ("POST", "notifications/read-all/"), ("PATCH", "notifications/preferences/"),
    ("POST", "notifications/push-tokens/"), ("DELETE", "notifications/push-tokens/abc/"),
    ("GET", "privacy/my-data/"), ("POST", "privacy/data-requests/"), ("PATCH", "me"),
]


@pytest.mark.parametrize("method,path", PARENT_ENDPOINTS)
def test_documented_parent_endpoint_resolves(method, path):
    url = "/api/v1/" + path
    for candidate in (url, url.rstrip("/"), url if url.endswith("/") else url + "/"):
        try:
            match = resolve(candidate)
        except Resolver404:
            continue
        actions = getattr(match.func, "actions", None)
        if actions is not None:  # DRF viewset route: the method must be mapped
            assert method.lower() in actions, (method, path)
        return
    pytest.fail(f"{method} {path} does not resolve")

import io
from decimal import Decimal

import pytest
from django.core.management import call_command

from conftest import assert_books_balanced
from tenants.models import School
from wallets.models import LedgerEntry, Wallet


@pytest.mark.django_db
def test_seed_demo_is_rerunnable_and_balanced():
    out = io.StringIO()
    call_command("seed_demo", stdout=out)
    assert "DEVICE_TOKEN=" in out.getvalue() and "TOPUP_LINK_TOKEN=" in out.getvalue()
    entries = LedgerEntry.objects.count()
    balances = dict(Wallet.objects.values_list("pk", "cached_balance"))
    call_command("seed_demo", stdout=io.StringIO())
    assert LedgerEntry.objects.count() == entries  # second run moves no money
    assert dict(Wallet.objects.values_list("pk", "cached_balance")) == balances
    assert_books_balanced(*School.objects.all())

    from disputes.models import Dispute
    from pooled_funds.models import PooledFund
    from pos.models import PosTransaction

    fund = PooledFund.objects.get()
    assert fund.wallet.cached_balance == Decimal("17500")
    assert PosTransaction.objects.filter(items__isnull=False).distinct().count() == 4
    assert Dispute.objects.filter(status="open").count() == 1

"""Part 2 cross-cutting ledger rules: double entry, system wallets, concurrency."""
import threading
from decimal import Decimal

import pytest
from django.db import IntegrityError, OperationalError, close_old_connections, connection

from conftest import assert_books_balanced, fund_wallet
from core.exceptions import InsufficientFundsError, InvalidWalletTypeError, LedgerError
from wallets.models import LedgerEntry, Wallet
from wallets.services import (
    ensure_student_wallets,
    get_system_wallet,
    post_ledger_entry,
    post_transfer,
)


@pytest.mark.django_db
class TestSystemWallets:
    def test_system_wallet_is_a_per_school_singleton(self, school_a, school_b):
        a1 = get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
        a2 = get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
        b1 = get_system_wallet(school_b, Wallet.WalletType.SCHOOL_SETTLEMENT)
        assert a1.pk == a2.pk != b1.pk
        assert a1.student is None and a1.is_system

    def test_db_forbids_second_singleton(self, school_a):
        get_system_wallet(school_a, Wallet.WalletType.AGGREGATOR_CLEARING)
        with pytest.raises(IntegrityError):
            Wallet.objects.create(school=school_a, wallet_type=Wallet.WalletType.AGGREGATOR_CLEARING)

    def test_db_forbids_student_wallet_without_student(self, school_a):
        with pytest.raises(IntegrityError):
            Wallet.objects.create(school=school_a, wallet_type=Wallet.WalletType.MAIN)

    def test_ensure_student_wallets_is_idempotent(self, student_a1):
        first = ensure_student_wallets(student_a1)
        second = ensure_student_wallets(student_a1)
        assert [w.pk for w in first] == [w.pk for w in second]

    def test_student_create_endpoint_creates_wallets(self, admin_a_client):
        resp = admin_a_client.post("/api/v1/students/", {"name": "New Kid", "class_name": "P1"})
        assert resp.status_code == 201
        types = set(Wallet.objects.filter(student_id=resp.data["id"]).values_list("wallet_type", flat=True))
        assert types == {"main", "savings"}


@pytest.mark.django_db
class TestPostTransfer:
    def test_transfer_moves_money_and_balances_books(self, school_a, student_a1):
        main, savings = ensure_student_wallets(student_a1)
        fund_wallet(main, "5000")
        post_transfer(
            debit_wallet=main, credit_wallet=savings, amount=Decimal("1200"),
            entry_type=LedgerEntry.EntryType.SAVINGS_MOVE_OUT,
            credit_entry_type=LedgerEntry.EntryType.SAVINGS_MOVE_IN,
            reference_id="t:1",
        )
        main.refresh_from_db(); savings.refresh_from_db()
        assert main.balance == Decimal("3800.00") and savings.balance == Decimal("1200.00")
        assert_books_balanced(school_a)

    def test_failed_transfer_leaves_no_trace(self, school_a, student_a1):
        main, savings = ensure_student_wallets(student_a1)
        fund_wallet(main, "100")
        before = LedgerEntry.objects.count()
        with pytest.raises(InsufficientFundsError):
            post_transfer(debit_wallet=main, credit_wallet=savings, amount=Decimal("500"),
                          entry_type="savings_move_out", reference_id="t:2")
        assert LedgerEntry.objects.count() == before
        assert_books_balanced(school_a)

    def test_only_clearing_wallet_may_go_negative(self, school_a, student_a1):
        main, _ = ensure_student_wallets(student_a1)
        settlement = get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
        with pytest.raises(InvalidWalletTypeError):
            post_ledger_entry(wallet=settlement, amount=Decimal("1"), direction="debit",
                              entry_type="refund", allow_negative=True)
        with pytest.raises(InsufficientFundsError):
            post_transfer(debit_wallet=settlement, credit_wallet=main, amount=Decimal("1"),
                          entry_type="refund", reference_id="t:3")

    def test_cross_school_transfer_rejected(self, student_a1, student_b1):
        a_main, _ = ensure_student_wallets(student_a1)
        b_main, _ = ensure_student_wallets(student_b1)
        fund_wallet(a_main, "100")
        with pytest.raises(LedgerError):
            post_transfer(debit_wallet=a_main, credit_wallet=b_main, amount=Decimal("10"),
                          entry_type="p2p_transfer_out", reference_id="t:4")

    def test_zero_and_negative_amounts_rejected(self, student_a1):
        main, savings = ensure_student_wallets(student_a1)
        for bad in ("0", "-5"):
            with pytest.raises(LedgerError):
                post_ledger_entry(wallet=main, amount=Decimal(bad), direction="credit", entry_type="deposit")


@pytest.mark.django_db(transaction=True)
def test_concurrent_debits_cannot_overspend(school_a, student_a1):
    """Two simultaneous 600 debits against a 1,000 balance: at most one can
    succeed. On Postgres the second waits on select_for_update and then sees
    insufficient funds; on SQLite the writer lock refuses it outright."""
    main, _ = ensure_student_wallets(student_a1)
    fund_wallet(main, "1000")
    settlement = get_system_wallet(school_a, Wallet.WalletType.SCHOOL_SETTLEMENT)
    barrier = threading.Barrier(2, timeout=10)
    outcomes = []

    def spend(n):
        close_old_connections()
        try:
            barrier.wait()
            post_transfer(debit_wallet=main, credit_wallet=settlement, amount=Decimal("600"),
                          entry_type="pos_purchase", reference_id=f"race:{n}")
            outcomes.append("ok")
        except (InsufficientFundsError, OperationalError, threading.BrokenBarrierError):
            outcomes.append("refused")
        finally:
            connection.close()

    threads = [threading.Thread(target=spend, args=(i,)) for i in range(2)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    main.refresh_from_db()
    if connection.vendor == "postgresql":
        # real row locking: one wins, the other waits then sees 400 left
        assert sorted(outcomes) == ["ok", "refused"]
    assert outcomes.count("ok") <= 1
    assert main.balance == Decimal("1000") - 600 * outcomes.count("ok")
    assert main.balance >= 0
    assert_books_balanced(school_a)

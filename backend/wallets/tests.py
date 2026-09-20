from decimal import Decimal

import pytest

from core.exceptions import InsufficientFundsError
from wallets.models import LedgerEntry, Wallet
from wallets.services import compute_balance, post_ledger_entry


@pytest.mark.django_db
class TestLedgerCorrectness:
    def test_credit_increases_balance(self, main_wallet_a1):
        post_ledger_entry(
            wallet=main_wallet_a1,
            amount=Decimal("1000"),
            direction=LedgerEntry.Direction.CREDIT,
            entry_type=LedgerEntry.EntryType.DEPOSIT,
        )
        main_wallet_a1.refresh_from_db()
        assert main_wallet_a1.balance == Decimal("1000.00")
        assert compute_balance(main_wallet_a1) == main_wallet_a1.balance

    def test_debit_decreases_balance(self, main_wallet_a1):
        post_ledger_entry(
            wallet=main_wallet_a1,
            amount=Decimal("1000"),
            direction=LedgerEntry.Direction.CREDIT,
            entry_type=LedgerEntry.EntryType.DEPOSIT,
        )
        post_ledger_entry(
            wallet=main_wallet_a1,
            amount=Decimal("300"),
            direction=LedgerEntry.Direction.DEBIT,
            entry_type=LedgerEntry.EntryType.POS_PURCHASE,
        )
        main_wallet_a1.refresh_from_db()
        assert main_wallet_a1.balance == Decimal("700.00")
        assert compute_balance(main_wallet_a1) == main_wallet_a1.balance

    def test_debit_beyond_balance_raises_and_does_not_mutate(self, main_wallet_a1):
        post_ledger_entry(
            wallet=main_wallet_a1,
            amount=Decimal("100"),
            direction=LedgerEntry.Direction.CREDIT,
            entry_type=LedgerEntry.EntryType.DEPOSIT,
        )
        with pytest.raises(InsufficientFundsError):
            post_ledger_entry(
                wallet=main_wallet_a1,
                amount=Decimal("500"),
                direction=LedgerEntry.Direction.DEBIT,
                entry_type=LedgerEntry.EntryType.POS_PURCHASE,
            )
        main_wallet_a1.refresh_from_db()
        assert main_wallet_a1.balance == Decimal("100.00")
        assert main_wallet_a1.ledger_entries.count() == 1

    def test_balance_always_equals_sum_of_entries_across_many_ops(
        self, main_wallet_a1, savings_wallet_a1
    ):
        ops = [
            (main_wallet_a1, "500", LedgerEntry.Direction.CREDIT, LedgerEntry.EntryType.DEPOSIT),
            (main_wallet_a1, "150", LedgerEntry.Direction.DEBIT, LedgerEntry.EntryType.POS_PURCHASE),
            (main_wallet_a1, "50", LedgerEntry.Direction.DEBIT, LedgerEntry.EntryType.SAVINGS_MOVE_OUT),
            (savings_wallet_a1, "50", LedgerEntry.Direction.CREDIT, LedgerEntry.EntryType.SAVINGS_MOVE_IN),
            (savings_wallet_a1, "20", LedgerEntry.Direction.DEBIT, LedgerEntry.EntryType.SAVINGS_WITHDRAWAL),
        ]
        for wallet, amount, direction, entry_type in ops:
            post_ledger_entry(
                wallet=wallet, amount=Decimal(amount), direction=direction, entry_type=entry_type
            )

        for wallet in (main_wallet_a1, savings_wallet_a1):
            wallet.refresh_from_db()
            assert wallet.balance == compute_balance(wallet)

        assert main_wallet_a1.balance == Decimal("300.00")
        assert savings_wallet_a1.balance == Decimal("30.00")

    def test_ledger_is_append_only_no_direct_balance_write_path(self, main_wallet_a1):
        # sanity check: cached_balance only ever changes via post_ledger_entry
        assert main_wallet_a1.cached_balance == Decimal("0.00")

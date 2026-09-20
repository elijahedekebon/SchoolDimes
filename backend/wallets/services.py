from decimal import Decimal

from django.db import transaction

from core.exceptions import InsufficientFundsError

from .models import LedgerEntry, Wallet


def compute_balance(wallet: Wallet) -> Decimal:
    """Recomputes a wallet's balance directly from its ledger entries.
    Used by tests/reconciliation to check `cached_balance` never drifts."""
    credits = wallet.ledger_entries.filter(direction=LedgerEntry.Direction.CREDIT)
    debits = wallet.ledger_entries.filter(direction=LedgerEntry.Direction.DEBIT)
    total_credits = sum((e.amount for e in credits), Decimal("0"))
    total_debits = sum((e.amount for e in debits), Decimal("0"))
    return total_credits - total_debits


@transaction.atomic
def post_ledger_entry(
    *,
    wallet: Wallet,
    amount: Decimal,
    direction: str,
    entry_type: str,
    reference_id: str = "",
    description: str = "",
) -> LedgerEntry:
    """
    The ONLY way money moves anywhere in this system. Locks the wallet row,
    creates the ledger entry, and updates the cached balance atomically.
    Raises InsufficientFundsError if a debit would take the wallet negative.
    """
    amount = Decimal(amount)
    locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    if direction == LedgerEntry.Direction.DEBIT and locked_wallet.cached_balance < amount:
        raise InsufficientFundsError(
            f"Wallet {locked_wallet.pk} balance {locked_wallet.cached_balance} "
            f"insufficient for debit of {amount}"
        )

    entry = LedgerEntry.objects.create(
        school_id=locked_wallet.school_id,
        wallet=locked_wallet,
        amount=amount,
        direction=direction,
        entry_type=entry_type,
        reference_id=reference_id,
        description=description,
    )

    if direction == LedgerEntry.Direction.CREDIT:
        locked_wallet.cached_balance += amount
    else:
        locked_wallet.cached_balance -= amount
    locked_wallet.save(update_fields=["cached_balance", "updated_at"])

    return entry

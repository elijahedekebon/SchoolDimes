from decimal import Decimal

from django.db import IntegrityError, transaction

from core.exceptions import InsufficientFundsError, InvalidWalletTypeError, LedgerError

from .models import LedgerEntry, Wallet
from .signals import ledger_entry_posted


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
    allow_negative: bool = False,
) -> LedgerEntry:
    """
    The ONLY way money moves anywhere in this system. Locks the wallet row,
    creates the ledger entry, and updates the cached balance atomically.
    Raises InsufficientFundsError if a debit would take the wallet negative.

    `allow_negative` (Part 2) is honoured only for `aggregator_clearing`
    system wallets, which are receivables and legitimately negative (see
    docs/DECISIONS.md "Chart of wallets"). Every other wallet type raises.
    Callers moving money between two wallets should use post_transfer().
    """
    amount = Decimal(amount)
    if amount <= 0:
        raise LedgerError(f"Ledger amounts must be positive, got {amount}")
    locked_wallet = Wallet.objects.select_for_update().get(pk=wallet.pk)

    if allow_negative and locked_wallet.wallet_type != Wallet.WalletType.AGGREGATOR_CLEARING:
        raise InvalidWalletTypeError(
            f"allow_negative is only permitted on aggregator_clearing wallets, "
            f"not {locked_wallet.wallet_type}"
        )

    if (
        direction == LedgerEntry.Direction.DEBIT
        and not allow_negative
        and locked_wallet.cached_balance < amount
    ):
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
    # keep the caller's instance in step so it doesn't need refresh_from_db()
    wallet.cached_balance = locked_wallet.cached_balance

    ledger_entry_posted.send(
        sender=LedgerEntry, entry=entry, balance_after=locked_wallet.cached_balance
    )
    return entry


@transaction.atomic
def post_transfer(
    *,
    debit_wallet: Wallet,
    credit_wallet: Wallet,
    amount: Decimal,
    entry_type: str,
    credit_entry_type: str | None = None,
    reference_id: str,
    description: str = "",
) -> tuple[LedgerEntry, LedgerEntry]:
    """
    Double-entry helper: debits one wallet and credits another for the same
    amount in one transaction, via two post_ledger_entry() calls sharing a
    `reference_id` (convention: "<kind>:<pk>", see API_CONTRACTS.md).

    Both wallets are locked up front in primary-key order so two opposite
    transfers can never deadlock. The debit side may go negative only if it
    is the aggregator clearing wallet (money arriving from outside).
    """
    if debit_wallet.pk == credit_wallet.pk:
        raise LedgerError("Cannot transfer a wallet to itself")
    if debit_wallet.school_id != credit_wallet.school_id:
        # Every wallet pair in one movement belongs to one tenant: merchant
        # settlement wallets exist per (merchant, school) for this reason.
        raise LedgerError("Both sides of a transfer must belong to the same school")
    list(
        Wallet.objects.select_for_update()
        .filter(pk__in=[debit_wallet.pk, credit_wallet.pk])
        .order_by("pk")
    )
    allow_negative = debit_wallet.wallet_type == Wallet.WalletType.AGGREGATOR_CLEARING
    debit = post_ledger_entry(
        wallet=debit_wallet,
        amount=amount,
        direction=LedgerEntry.Direction.DEBIT,
        entry_type=entry_type,
        reference_id=reference_id,
        description=description,
        allow_negative=allow_negative,
    )
    credit = post_ledger_entry(
        wallet=credit_wallet,
        amount=amount,
        direction=LedgerEntry.Direction.CREDIT,
        entry_type=credit_entry_type or entry_type,
        reference_id=reference_id,
        description=description,
    )
    return debit, credit


def _get_or_create_race_safe(**lookup) -> Wallet:
    try:
        with transaction.atomic():
            wallet, _ = Wallet.objects.get_or_create(**lookup)
            return wallet
    except IntegrityError:
        return Wallet.objects.get(**lookup)


def get_system_wallet(school, wallet_type: str) -> Wallet:
    """The per-school singleton system wallets: school_settlement and
    aggregator_clearing. Created lazily; a DB constraint guarantees one."""
    if wallet_type not in (
        Wallet.WalletType.SCHOOL_SETTLEMENT,
        Wallet.WalletType.AGGREGATOR_CLEARING,
    ):
        raise InvalidWalletTypeError(f"{wallet_type} is not a per-school system wallet")
    school_id = getattr(school, "pk", school)
    return _get_or_create_race_safe(school_id=school_id, wallet_type=wallet_type, student=None)


def get_student_wallet(student, wallet_type: str = Wallet.WalletType.MAIN) -> Wallet:
    if wallet_type not in (Wallet.WalletType.MAIN, Wallet.WalletType.SAVINGS):
        raise InvalidWalletTypeError(f"{wallet_type} is not a student wallet type")
    return _get_or_create_race_safe(
        student=student, wallet_type=wallet_type, school_id=student.school_id
    )


def ensure_student_wallets(student) -> tuple[Wallet, Wallet]:
    """Creates the student's main + savings wallets if missing (called at
    student onboarding; Part 1 only created them in seed_demo)."""
    return (
        get_student_wallet(student, Wallet.WalletType.MAIN),
        get_student_wallet(student, Wallet.WalletType.SAVINGS),
    )


def school_books_total(school) -> Decimal:
    """Sum of every wallet balance in a school. Because every Part 2+
    movement is a balanced transfer, this is always exactly zero."""
    total = Decimal("0")
    for wallet in Wallet.objects.filter(school=school):
        total += wallet.cached_balance
    return total

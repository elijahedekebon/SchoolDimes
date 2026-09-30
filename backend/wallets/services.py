from dataclasses import dataclass, field
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


# ---------------------------------------------------------------------------
# The one debit gate (Part 2, cross-cutting rule 4)
# ---------------------------------------------------------------------------

class DebitKind:
    PURCHASE = "purchase"  # canteen or merchant sale (POS / online purchase)
    P2P = "p2p"
    FEE_PAYMENT = "fee_payment"
    SAVINGS_MOVE = "savings_move"
    SAVINGS_WITHDRAWAL = "savings_withdrawal"


@dataclass
class DebitContext:
    kind: str
    card: object = None  # the Card presented, if any
    items: list = field(default_factory=list)  # [{"product_id": .., "category_id": ..}]
    merchant_id: int | None = None
    now: object = None


@dataclass
class DebitDecision:
    allowed: bool
    code: str = ""
    message: str = ""
    violations: list = field(default_factory=list)


def debit_violations(wallet: Wallet, amount: Decimal, context: DebitContext, *, check_balance=True) -> list[str]:
    """
    Every rule a debit breaks, in priority order (empty list = allowed).
    Checks card/wallet status, balance, and the student's effective Policy:
    purchases -> per-transaction / daily / weekly caps, categories, items,
    merchants; p2p -> p2p_enabled and p2p_daily_cap. Fee payments, savings
    moves and savings withdrawals are exempt from spending caps.
    The POS offline sync path uses this with check_balance=False to *flag*
    (not refuse) a sale that already happened.
    """
    from policies.services import get_effective_policy, p2p_sent_today, spent_this_week, spent_today

    amount = Decimal(amount)
    if wallet.is_system:
        return ["wallet_not_spendable"]
    violations = []
    student = wallet.student

    card = context.card
    if card is not None:
        if card.status == "frozen":
            violations.append("card_frozen")
        elif card.status == "lost":
            violations.append("card_lost")
    elif student.cards.filter(status="frozen").exists():
        # Freeze blocks every debit, including guardian-initiated ones.
        violations.append("card_frozen")

    if check_balance and wallet.cached_balance < amount:
        violations.append("insufficient_funds")

    if context.kind in (DebitKind.PURCHASE, DebitKind.P2P):
        policy = get_effective_policy(student)
    if context.kind == DebitKind.PURCHASE:
        if policy.per_transaction_cap is not None and amount > policy.per_transaction_cap:
            violations.append("per_transaction_cap_exceeded")
        if policy.daily_spend_cap is not None and spent_today(wallet, context.now) + amount > policy.daily_spend_cap:
            violations.append("daily_cap_exceeded")
        if policy.weekly_spend_cap is not None and spent_this_week(wallet, context.now) + amount > policy.weekly_spend_cap:
            violations.append("weekly_cap_exceeded")
        category_ids = {i.get("category_id") for i in context.items if i.get("category_id")}
        product_ids = {i.get("product_id") for i in context.items if i.get("product_id")}
        if category_ids & policy.blocked_category_ids:
            violations.append("category_blocked")
        if policy.allowed_category_ids is not None and category_ids - policy.allowed_category_ids:
            violations.append("category_not_allowed")
        if product_ids & policy.blocked_product_ids:
            violations.append("item_blocked")
        if context.merchant_id and (
            context.merchant_id in policy.blocked_merchant_ids
            or (policy.allowed_merchant_ids is not None and context.merchant_id not in policy.allowed_merchant_ids)
        ):
            violations.append("merchant_blocked")
    elif context.kind == DebitKind.P2P:
        if not policy.p2p_enabled:
            violations.append("p2p_disabled")
        elif policy.p2p_daily_cap is not None and p2p_sent_today(wallet, context.now) + amount > policy.p2p_daily_cap:
            violations.append("p2p_cap_exceeded")
    return violations


def authorize_debit(wallet: Wallet, amount: Decimal, context: DebitContext) -> DebitDecision:
    """
    The single gate every debit path calls before post_ledger_entry()/
    post_transfer(): POS/merchant purchases, P2P, fee payments, savings moves
    and withdrawals. MUST be called inside transaction.atomic(): it locks the
    wallet row (select_for_update) so the balance and cap checks can't race
    a concurrent debit. Returns a DebitDecision; use require_debit() to raise.
    """
    from policies.services import refusal_message

    locked = Wallet.objects.select_for_update(of=("self",)).select_related("student").get(pk=wallet.pk)
    violations = debit_violations(locked, amount, context)
    if violations:
        code = violations[0]
        return DebitDecision(False, code, refusal_message(code), violations)
    return DebitDecision(True)


def require_debit(wallet: Wallet, amount: Decimal, context: DebitContext) -> None:
    """authorize_debit() that raises core.exceptions.DebitRefused (HTTP 422)."""
    from core.exceptions import DebitRefused

    decision = authorize_debit(wallet, amount, context)
    if not decision.allowed:
        raise DebitRefused(decision.code, decision.message, extra={"violations": decision.violations})

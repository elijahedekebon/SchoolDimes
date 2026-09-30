from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


STUDENT_WALLET_TYPES = ["main", "savings"]
SCHOOL_SINGLETON_WALLET_TYPES = ["school_settlement", "aggregator_clearing"]


class Wallet(models.Model):
    """
    Student wallets (`main`, `savings`) plus, since Part 2, system wallets
    that are the other side of every double-entry movement (see the chart
    of wallets in docs/DATA_MODEL.md). System wallets have `student=null`.
    """

    class WalletType(models.TextChoices):
        MAIN = "main", "Main"
        SAVINGS = "savings", "Savings"
        # --- system wallets (Part 2) ---
        SCHOOL_SETTLEMENT = "school_settlement", "School settlement"
        AGGREGATOR_CLEARING = "aggregator_clearing", "Aggregator clearing"
        POOLED_FUND = "pooled_fund", "Pooled fund"
        MERCHANT_SETTLEMENT = "merchant_settlement", "Merchant settlement"

    school = models.ForeignKey(
        "tenants.School", on_delete=models.CASCADE, related_name="wallets"
    )
    student = models.ForeignKey(
        "students.Student",
        on_delete=models.CASCADE,
        related_name="wallets",
        null=True,
        blank=True,
        help_text="Set for main/savings wallets; null for system wallets.",
    )
    wallet_type = models.CharField(max_length=24, choices=WalletType.choices)
    # Cached/derived from LedgerEntry rows. NEVER written directly outside
    # wallets.services.post_ledger_entry -- see compute_balance() for the
    # source of truth this cache is checked against.
    cached_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    # Part 2: parent-configured window in which savings may be withdrawn to
    # mobile money (savings wallets only; both null = withdrawals closed).
    withdrawal_window_start = models.DateTimeField(null=True, blank=True)
    withdrawal_window_end = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["student", "wallet_type"]
        ordering = ["student", "wallet_type"]
        constraints = [
            models.CheckConstraint(
                condition=(
                    models.Q(wallet_type__in=STUDENT_WALLET_TYPES, student__isnull=False)
                    | (
                        ~models.Q(wallet_type__in=STUDENT_WALLET_TYPES)
                        & models.Q(student__isnull=True)
                    )
                ),
                name="wallet_student_matches_type",
            ),
            models.UniqueConstraint(
                fields=["school", "wallet_type"],
                condition=models.Q(wallet_type__in=SCHOOL_SINGLETON_WALLET_TYPES),
                name="one_school_system_wallet_per_type",
            ),
        ]

    def __str__(self):
        if self.student_id:
            return f"{self.student} - {self.wallet_type} wallet"
        return f"{self.school} - {self.wallet_type} wallet #{self.pk}"

    @property
    def balance(self) -> Decimal:
        return self.cached_balance

    @property
    def is_system(self) -> bool:
        return self.wallet_type not in STUDENT_WALLET_TYPES


class LedgerEntry(models.Model):
    class Direction(models.TextChoices):
        CREDIT = "credit", "Credit"
        DEBIT = "debit", "Debit"

    class EntryType(models.TextChoices):
        DEPOSIT = "deposit", "Deposit"
        POS_PURCHASE = "pos_purchase", "POS Purchase"
        P2P_TRANSFER_OUT = "p2p_transfer_out", "P2P Transfer Out"
        P2P_TRANSFER_IN = "p2p_transfer_in", "P2P Transfer In"
        SAVINGS_MOVE_IN = "savings_move_in", "Savings Move In"
        SAVINGS_MOVE_OUT = "savings_move_out", "Savings Move Out"
        SAVINGS_WITHDRAWAL = "savings_withdrawal", "Savings Withdrawal"
        REFUND = "refund", "Refund"
        FEE_PAYMENT = "fee_payment", "Fee Payment"
        GIFT_VOUCHER = "gift_voucher", "Gift Voucher"
        POOLED_FUND_CONTRIBUTION = "pooled_fund_contribution", "Pooled Fund Contribution"
        POOLED_FUND_DISBURSEMENT = "pooled_fund_disbursement", "Pooled Fund Disbursement"
        # --- Part 2 ---
        REVERSAL = "reversal", "Reversal"
        SHORTFALL_RECOVERY = "shortfall_recovery", "Shortfall Recovery"

    school = models.ForeignKey(
        "tenants.School", on_delete=models.CASCADE, related_name="ledger_entries"
    )
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="ledger_entries")
    amount = models.DecimalField(
        max_digits=12, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))]
    )
    direction = models.CharField(max_length=10, choices=Direction.choices)
    entry_type = models.CharField(max_length=32, choices=EntryType.choices)
    reference_id = models.CharField(
        max_length=64, blank=True, help_text="Id of the source object (POS sale, transfer, etc.)"
    )
    description = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "Ledger entries"

    def __str__(self):
        return f"{self.wallet} {self.direction} {self.amount} ({self.entry_type})"


class SavingsGoal(models.Model):
    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name="savings_goals",
        limit_choices_to={"wallet_type": Wallet.WalletType.SAVINGS},
    )
    goal_name = models.CharField(max_length=255)
    target_amount = models.DecimalField(max_digits=12, decimal_places=2)
    target_date = models.DateField(null=True, blank=True)
    reached_at = models.DateTimeField(
        null=True, blank=True, help_text="Set once, when savings first reach target_amount (Part 2)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.wallet_id and self.wallet.wallet_type != Wallet.WalletType.SAVINGS:
            raise ValidationError("SavingsGoal.wallet must be a savings wallet.")

    def __str__(self):
        return f"{self.goal_name} ({self.wallet.student})"


class P2PTransfer(models.Model):
    """Student-to-student transfer (same school only). Ledger: sender main
    debit `p2p_transfer_out`, recipient main credit `p2p_transfer_in`,
    reference_id "p2p:<id>"."""

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="p2p_transfers")
    sender_wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="p2p_sent")
    recipient_wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name="p2p_received")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    note = models.CharField(max_length=140, blank=True)
    initiated_by = models.ForeignKey(
        "accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+",
        help_text="Guardian who initiated it (null when initiated at a POS device).",
    )
    device_id_ref = models.BigIntegerField(
        null=True, blank=True, help_text="pos.Device id when initiated at a POS device with card + PIN."
    )
    idempotency_key = models.CharField(
        max_length=128, unique=True, null=True, blank=True, help_text="Set by POS-initiated transfers (retries)."
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class P2PAlert(models.Model):
    """Rule-based "pressure or bullying" flag for school_admin review (§5)."""

    class Rule(models.TextChoices):
        MANY_DISTINCT_SENDERS = "many_distinct_senders", "Many distinct senders"
        REPEATED_NEAR_CAP = "repeated_near_cap", "Repeatedly sending near the cap"

    class Status(models.TextChoices):
        OPEN = "open", "Open"
        REVIEWED = "reviewed", "Reviewed"
        DISMISSED = "dismissed", "Dismissed"

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="p2p_alerts")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="p2p_alerts")
    rule = models.CharField(max_length=32, choices=Rule.choices)
    details = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    reviewed_by = models.ForeignKey("accounts.User", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

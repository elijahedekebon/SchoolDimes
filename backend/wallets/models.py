from decimal import Decimal

from django.core.validators import MinValueValidator
from django.db import models


class Wallet(models.Model):
    class WalletType(models.TextChoices):
        MAIN = "main", "Main"
        SAVINGS = "savings", "Savings"

    school = models.ForeignKey(
        "tenants.School", on_delete=models.CASCADE, related_name="wallets"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="wallets"
    )
    wallet_type = models.CharField(max_length=10, choices=WalletType.choices)
    # Cached/derived from LedgerEntry rows. NEVER written directly outside
    # wallets.services.post_ledger_entry -- see compute_balance() for the
    # source of truth this cache is checked against.
    cached_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["student", "wallet_type"]
        ordering = ["student", "wallet_type"]

    def __str__(self):
        return f"{self.student} - {self.wallet_type} wallet"

    @property
    def balance(self) -> Decimal:
        return self.cached_balance


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
    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.wallet_id and self.wallet.wallet_type != Wallet.WalletType.SAVINGS:
            raise ValidationError("SavingsGoal.wallet must be a savings wallet.")

    def __str__(self):
        return f"{self.goal_name} ({self.wallet.student})"

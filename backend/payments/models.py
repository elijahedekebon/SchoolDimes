from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Channel(models.TextChoices):
    MOMO = "momo", _("Mobile money")
    BANK = "bank", _("Bank transfer")
    USSD = "ussd", _("USSD")


class Contributor(models.Model):
    """Someone topping up a student without a SchoolDimes account (a
    grandparent, aunt, sponsor...). Distinct from Guardian: no login, no
    visibility into the student's data. One row per contribution."""

    name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=20, blank=True)
    email = models.EmailField(blank=True)
    relationship_label = models.CharField(max_length=64, blank=True, help_text="e.g. 'Grandmother'")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class StudentTopUpLink(models.Model):
    """A shareable, revocable link letting contributors top up one student."""

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="+")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="topup_links")
    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.PROTECT, related_name="topup_links")
    token = models.CharField(max_length=64, unique=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="topup_links")
    active = models.BooleanField(default=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class Deposit(models.Model):
    """
    A collection of money INTO the platform through the aggregator. One
    model covers all three collection purposes so there is exactly one
    confirmation path (payments.services.process_payment_event):
      wallet_topup             -> credits a student main/savings wallet
      gift_voucher             -> credits the student's main wallet (see GiftVoucher)
      pooled_fund_contribution -> credits a pooled fund's system wallet
    Money moves ONLY when the aggregator confirms, never at initiation.
    """

    class Purpose(models.TextChoices):
        WALLET_TOPUP = "wallet_topup", _("Wallet top-up")
        GIFT_VOUCHER = "gift_voucher", _("Gift voucher")
        POOLED_FUND_CONTRIBUTION = "pooled_fund_contribution", _("Pooled fund contribution")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        CONFIRMED = "confirmed", _("Confirmed")
        FAILED = "failed", _("Failed")
        EXPIRED = "expired", _("Expired")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="deposits")
    purpose = models.CharField(max_length=32, choices=Purpose.choices, default=Purpose.WALLET_TOPUP)
    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.PROTECT, related_name="deposits")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    channel = models.CharField(max_length=10, choices=Channel.choices)
    payer_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=40, unique=True, help_text="Ours; echoed back by the aggregator.")
    aggregator_ref = models.CharField(max_length=64, unique=True, null=True, blank=True)
    instructions = models.JSONField(default=dict, blank=True)
    initiated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="deposits"
    )
    contributor = models.ForeignKey(
        Contributor, on_delete=models.SET_NULL, null=True, blank=True, related_name="deposits"
    )
    recurring_topup = models.ForeignKey(
        "payments.RecurringTopUp", on_delete=models.SET_NULL, null=True, blank=True, related_name="deposits"
    )
    idempotency_key = models.CharField(max_length=128, unique=True)
    failure_reason = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return f"Deposit {self.reference} {self.amount} ({self.status})"


class Payout(models.Model):
    """Money OUT of the platform to a phone via the aggregator (savings
    withdrawals, external pooled-fund disbursements). The source wallet is
    debited when the payout is initiated; a failure posts a compensating
    `reversal` entry -- nothing is ever deleted."""

    class Purpose(models.TextChoices):
        SAVINGS_WITHDRAWAL = "savings_withdrawal", _("Savings withdrawal")
        POOLED_FUND_DISBURSEMENT = "pooled_fund_disbursement", _("Pooled fund disbursement")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SUCCEEDED = "succeeded", _("Succeeded")
        FAILED = "failed", _("Failed")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="payouts")
    purpose = models.CharField(max_length=32, choices=Purpose.choices)
    source_wallet = models.ForeignKey("wallets.Wallet", on_delete=models.PROTECT, related_name="payouts")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    phone_number = models.CharField(max_length=20)
    description = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    reference = models.CharField(max_length=40, unique=True)
    aggregator_ref = models.CharField(max_length=64, unique=True, null=True, blank=True)
    idempotency_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="payouts"
    )
    failure_reason = models.CharField(max_length=64, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]


class GiftVoucher(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", _("Pending payment")
        PAID = "paid", _("Paid")
        REDEEMED = "redeemed", _("Redeemed")
        CANCELLED = "cancelled", _("Cancelled")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="+")
    sender_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="gift_vouchers_sent"
    )
    sender_contributor = models.ForeignKey(
        Contributor, on_delete=models.SET_NULL, null=True, blank=True, related_name="gift_vouchers"
    )
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="gift_vouchers")
    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.PROTECT, related_name="gift_vouchers")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    message = models.CharField(max_length=280, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT)
    deposit = models.OneToOneField(Deposit, on_delete=models.PROTECT, related_name="gift_voucher")
    redeemed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    @property
    def sender_name(self):
        if self.sender_user_id:
            return self.sender_user.full_name or self.sender_user.email
        return self.sender_contributor.name if self.sender_contributor_id else ""


class RecurringTopUp(models.Model):
    class Frequency(models.TextChoices):
        WEEKLY = "weekly", _("Weekly")
        MONTHLY = "monthly", _("Monthly")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="+")
    parent = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="recurring_topups")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="recurring_topups")
    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.PROTECT, related_name="recurring_topups")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.MOMO)
    payer_phone = models.CharField(max_length=20)
    frequency = models.CharField(max_length=10, choices=Frequency.choices)
    day_of_week = models.PositiveSmallIntegerField(null=True, blank=True, help_text="0=Monday .. 6=Sunday (weekly)")
    day_of_month = models.PositiveSmallIntegerField(null=True, blank=True, help_text="1..28 (monthly)")
    next_run_at = models.DateTimeField()
    active = models.BooleanField(default=True)
    last_run_at = models.DateTimeField(null=True, blank=True)
    last_status = models.CharField(max_length=20, blank=True)
    consecutive_failures = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["next_run_at"]


class UnmatchedWebhook(models.Model):
    """Webhooks we could not apply (unknown reference, amount mismatch, late
    success after failure). Answered 200 so the aggregator stops retrying,
    kept here for admin review (Django admin)."""

    reference = models.CharField(max_length=64, blank=True)
    aggregator_ref = models.CharField(max_length=64, blank=True)
    reason = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)
    reviewed = models.BooleanField(default=False)
    received_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-received_at"]

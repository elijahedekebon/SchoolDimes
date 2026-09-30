from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class PooledFund(models.Model):
    """A transparent group collection (class trip, teacher's gift...). Money
    sits in its own `pooled_fund` system wallet; the ledger is the truth."""

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        CLOSED = "closed", _("Closed")
        DISBURSED = "disbursed", _("Disbursed")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="pooled_funds")
    title = models.CharField(max_length=255)
    purpose = models.TextField(blank=True)
    group_label = models.CharField(max_length=100, blank=True, help_text="Class/group, e.g. 'P4 Blue'")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pooled_funds_created")
    target_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    deadline = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.OPEN)
    wallet = models.OneToOneField("wallets.Wallet", on_delete=models.PROTECT, related_name="pooled_fund")
    created_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-id"]

    def __str__(self):
        return self.title


class PooledFundContribution(models.Model):
    """Written when a pooled-fund Deposit is CONFIRMED (never at initiation)."""

    fund = models.ForeignKey(PooledFund, on_delete=models.PROTECT, related_name="contributions")
    contributor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    contributor = models.ForeignKey(
        "payments.Contributor", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    deposit = models.OneToOneField("payments.Deposit", on_delete=models.PROTECT, related_name="pooled_fund_contribution")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

    @property
    def contributor_name(self):
        if self.contributor_user_id:
            return self.contributor_user.full_name or self.contributor_user.email
        return self.contributor.name if self.contributor_id else ""


class PooledFundDisbursement(models.Model):
    class Destination(models.TextChoices):
        SCHOOL_SETTLEMENT = "school_settlement", _("School settlement wallet")
        EXTERNAL = "external", _("External payout (mobile money)")

    fund = models.ForeignKey(PooledFund, on_delete=models.PROTECT, related_name="disbursements")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    destination = models.CharField(max_length=20, choices=Destination.choices)
    description = models.CharField(max_length=255)
    payout = models.OneToOneField("payments.Payout", on_delete=models.PROTECT, null=True, blank=True, related_name="+")
    disbursed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]

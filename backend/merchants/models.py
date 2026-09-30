from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Merchant(models.Model):
    """An approved nearby merchant (proposal §4.3). A merchant may serve
    several schools; each school approves or suspends it independently via
    MerchantApproval. `status` is the platform-level switch (platform_admin);
    a merchant can charge a school's cards only while BOTH its own status and
    that school's approval are `approved`."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        SUSPENDED = "suspended", _("Suspended")

    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100, blank=True, help_text="e.g. bookshop, tailor, pharmacy")
    contact_phone = models.CharField(max_length=20, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.APPROVED)
    approved_for_schools = models.ManyToManyField(
        "tenants.School", through="MerchantApproval", related_name="merchants", blank=True
    )
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class MerchantApproval(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPROVED = "approved", _("Approved")
        SUSPENDED = "suspended", _("Suspended")

    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="approvals")
    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="merchant_approvals")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    decided_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["merchant", "school"], name="one_approval_per_merchant_school")]


class MerchantStaff(models.Model):
    """Links a merchant_staff user to their merchant (User itself is Part 1
    and untouched)."""

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="merchant_link")
    merchant = models.ForeignKey(Merchant, on_delete=models.CASCADE, related_name="staff")
    created_at = models.DateTimeField(auto_now_add=True)

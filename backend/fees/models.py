from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class FeeCategory(models.Model):
    """A school fee payable from a student's wallet (uniform, trip, exam...)."""

    class AmountType(models.TextChoices):
        FIXED = "fixed", _("Fixed amount")
        RANGE = "range", _("Any amount within a range")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="fee_categories")
    name = models.CharField(max_length=100)
    amount_type = models.CharField(max_length=10, choices=AmountType.choices, default=AmountType.FIXED)
    fixed_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    min_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    max_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    active = models.BooleanField(default=True)
    due_date = models.DateField(null=True, blank=True)
    applicable_classes = models.JSONField(
        default=list, blank=True, help_text="List of Student.class_name values; empty = every class."
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "Fee categories"

    def __str__(self):
        return self.name


class FeePayment(models.Model):
    """A completed fee payment (student main wallet -> school settlement).
    Refused payments are not stored; the API returns the refusal code."""

    class Status(models.TextChoices):
        COMPLETED = "completed", _("Completed")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="fee_payments")
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="fee_payments")
    fee_category = models.ForeignKey(FeeCategory, on_delete=models.PROTECT, related_name="payments")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    paid_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="fee_payments")
    ledger_reference = models.CharField(max_length=64, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.COMPLETED)
    idempotency_key = models.CharField(max_length=128, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

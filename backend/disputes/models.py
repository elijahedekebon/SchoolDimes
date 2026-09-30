from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

OPEN_STATUSES = ["open", "under_review"]


class Dispute(models.Model):
    """A guardian's challenge of a debit. Exactly one of pos_transaction /
    ledger_entry is set. At most one OPEN dispute per transaction (DB
    constraint); after resolution a new one may be raised, but total refunds
    on a transaction can never exceed what was actually debited."""

    class ReasonCategory(models.TextChoices):
        WRONG_AMOUNT = "wrong_amount", _("Charged the wrong amount")
        NOT_RECEIVED = "not_received", _("Paid but item/service not received")
        UNAUTHORIZED = "unauthorized", _("Not made by my child")
        DUPLICATE = "duplicate", _("Charged twice")
        OTHER = "other", _("Other")

    class Status(models.TextChoices):
        OPEN = "open", _("Open")
        UNDER_REVIEW = "under_review", _("Under review")
        RESOLVED_REFUNDED = "resolved_refunded", _("Resolved — refunded")
        RESOLVED_DENIED = "resolved_denied", _("Resolved — not refunded")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="disputes")
    raised_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="disputes_raised")
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, related_name="disputes")
    pos_transaction = models.ForeignKey("pos.PosTransaction", on_delete=models.PROTECT, null=True, blank=True, related_name="disputes")
    ledger_entry = models.ForeignKey("wallets.LedgerEntry", on_delete=models.PROTECT, null=True, blank=True, related_name="disputes")
    reason_category = models.CharField(max_length=20, choices=ReasonCategory.choices)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.OPEN)
    resolution_notes = models.TextField(blank=True)
    refund_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    resolved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["pos_transaction"], condition=models.Q(status__in=OPEN_STATUSES),
                                    name="one_open_dispute_per_pos_transaction"),
            models.UniqueConstraint(fields=["ledger_entry"], condition=models.Q(status__in=OPEN_STATUSES),
                                    name="one_open_dispute_per_ledger_entry"),
            models.CheckConstraint(
                condition=(models.Q(pos_transaction__isnull=False, ledger_entry__isnull=True)
                           | models.Q(pos_transaction__isnull=True, ledger_entry__isnull=False)),
                name="dispute_has_exactly_one_target",
            ),
        ]

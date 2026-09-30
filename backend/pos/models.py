from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class Device(models.Model):
    """A POS / merchant / attendance device. Authenticates with a device
    token (`Authorization: Device <token>`); only a SHA-256 hash is stored."""

    class Role(models.TextChoices):
        CANTEEN = "canteen", _("Canteen")
        MERCHANT = "merchant", _("Merchant")
        ATTENDANCE = "attendance", _("Attendance")

    class Status(models.TextChoices):
        ACTIVE = "active", _("Active")
        REVOKED = "revoked", _("Revoked")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="devices")
    device_name = models.CharField(max_length=100)
    device_role = models.CharField(max_length=12, choices=Role.choices)
    token_hash = models.CharField(max_length=64, unique=True)
    token_prefix = models.CharField(max_length=8, help_text="First characters of the token, for identification only.")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    last_seen_at = models.DateTimeField(null=True, blank=True)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    app_version = models.CharField(max_length=32, blank=True)
    registered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+")
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["school", "device_name"]

    def __str__(self):
        return f"{self.device_name} ({self.device_role})"


class PosTransaction(models.Model):
    """One sale, recorded exactly once per (device, idempotency_key).
    A sale made offline is ALWAYS recorded (it already happened at the
    counter); breaches become a shortfall and/or flags for admin review."""

    class Channel(models.TextChoices):
        OFFLINE_SYNC = "offline_sync", _("Offline, synced later")
        ONLINE = "online", _("Online")

    class SyncStatus(models.TextChoices):
        APPLIED = "applied", _("Applied")
        SHORTFALL = "shortfall", _("Applied with shortfall")
        REJECTED = "rejected", _("Rejected")

    class ReviewStatus(models.TextChoices):
        NONE = "none", _("No review needed")
        PENDING = "pending", _("Pending review")
        RECOVERY_PENDING = "recovery_pending", _("Recovering shortfall")
        RESOLVED = "resolved", _("Resolved")

    class Resolution(models.TextChoices):
        ACCEPT = "accept", _("Accepted as is")
        WRITE_OFF = "write_off", _("Written off")
        RECOVER_FROM_NEXT_TOPUP = "recover_from_next_topup", _("Recover from next top-up")
        CHARGE_GUARDIAN = "charge_guardian", _("Charge the guardian")

    device = models.ForeignKey(Device, on_delete=models.PROTECT, related_name="transactions")
    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="pos_transactions",
                               help_text="The card holder's school (the tenant the money belongs to).")
    card = models.ForeignKey("cards.Card", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_transactions")
    card_uid = models.CharField(max_length=64, help_text="As sent by the device (kept even if unknown).")
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_transactions")
    wallet = models.ForeignKey("wallets.Wallet", on_delete=models.PROTECT, null=True, blank=True, related_name="pos_transactions")
    channel = models.CharField(max_length=12, choices=Channel.choices, default=Channel.OFFLINE_SYNC)
    amount = models.DecimalField(max_digits=12, decimal_places=2, help_text="Sale total as rung up.")
    applied_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Actually debited.")
    shortfall_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    recovered_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    idempotency_key = models.CharField(max_length=128)
    device_local_timestamp = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)
    sync_status = models.CharField(max_length=10, choices=SyncStatus.choices)
    reject_reason = models.CharField(max_length=64, blank=True)
    flags = models.JSONField(default=list, blank=True, help_text="Policy/card rule codes the sale broke.")
    pin_verified = models.BooleanField(null=True, blank=True)
    ledger_reference = models.CharField(max_length=64, blank=True)
    review_status = models.CharField(max_length=20, choices=ReviewStatus.choices, default=ReviewStatus.NONE)
    resolution = models.CharField(max_length=32, choices=Resolution.choices, blank=True)
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    reviewed_at = models.DateTimeField(null=True, blank=True)
    review_notes = models.TextField(blank=True)

    class Meta:
        ordering = ["-received_at", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["device", "idempotency_key"], name="pos_txn_idempotent_per_device"),
        ]
        indexes = [models.Index(fields=["school", "review_status"])]


class PosTransactionItem(models.Model):
    transaction = models.ForeignKey(PosTransaction, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey("policies.Product", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    description = models.CharField(max_length=255)
    category = models.ForeignKey("policies.ProductCategory", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    quantity = models.PositiveIntegerField(default=1)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2)


class PinFailureReport(models.Model):
    """Wrong-PIN attempts reported by devices (offline via sync, or online)."""

    device = models.ForeignKey(Device, on_delete=models.CASCADE, related_name="pin_failures")
    card = models.ForeignKey("cards.Card", on_delete=models.CASCADE, related_name="pin_failures")
    failed_attempts = models.PositiveSmallIntegerField(default=1)
    device_local_timestamp = models.DateTimeField(null=True, blank=True)
    received_at = models.DateTimeField(auto_now_add=True)

from django.db import models
from django.utils.translation import gettext_lazy as _


class School(models.Model):
    """The tenant. Every other tenant-scoped model carries a `school` FK
    derived (server-side) from the authenticated user, never client input."""

    name = models.CharField(max_length=255)
    address = models.TextField(blank=True)
    branding = models.JSONField(
        default=dict,
        blank=True,
        help_text="e.g. {'logo_url': ..., 'primary_color': '#123456'}",
    )
    supported_languages = models.JSONField(
        default=list,
        blank=True,
        help_text="Subset of ['en', 'lg', 'sw'] this school offers to its users.",
    )
    policy_defaults = models.JSONField(
        default=dict,
        blank=True,
        help_text="Default spending caps / category restrictions / blocked items "
        "applied to new cards at this school. Enforcement is Part 2.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class SchoolReferral(models.Model):
    """Proposal S9: schools that refer other schools earn a reward once
    the referred school's signup is applied. The actual discount/billing
    mechanics are a business/finance concern, documented as a placeholder
    in docs/DECISIONS.md -- this model only tracks the relationship."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        APPLIED = "applied", _("Applied")
        REJECTED = "rejected", _("Rejected")

    referring_school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="referrals_made"
    )
    referred_school = models.ForeignKey(
        School, on_delete=models.CASCADE, related_name="referrals_received"
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    reward_applied = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(referring_school=models.F("referred_school")),
                name="referral_cannot_self_reference",
            )
        ]

    def __str__(self):
        return f"{self.referring_school} -> {self.referred_school} ({self.status})"


class SchoolSettings(models.Model):
    """Part 2: per-school operational settings (one row per school, created
    lazily by tenants.services.get_school_settings)."""

    school = models.OneToOneField(School, on_delete=models.CASCADE, related_name="settings")
    offline_spend_ceiling = models.DecimalField(
        max_digits=12, decimal_places=2, default=2000,
        help_text="How far (UGX) a card may go below its cached balance across offline POS devices.",
    )
    pin_lockout_threshold = models.PositiveSmallIntegerField(
        default=5, help_text="Wrong PINs reported within 24h that freeze a card."
    )
    device_stale_after_hours = models.PositiveSmallIntegerField(
        default=24, help_text="A device that hasn't synced for this long is reported stale."
    )
    attendance_notify_guardians = models.BooleanField(
        default=False, help_text="Notify guardians on a student's first tap-in of the day."
    )
    attendance_on_canteen_devices = models.BooleanField(
        default=False, help_text="Allow canteen devices to record attendance taps too."
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "School settings"

    def __str__(self):
        return f"Settings({self.school_id})"

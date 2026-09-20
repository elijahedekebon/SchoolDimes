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

from django.db import models

from accounts.models import User


class FinancialLiteracyTip(models.Model):
    """
    Translation model: each language gets its OWN row (not per-field i18n),
    so seeding "the same tip" in en/lg/sw means three rows. school=null
    means the tip is platform-wide; otherwise it is scoped to one school.
    """

    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.CASCADE,
        related_name="financial_literacy_tips",
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=255)
    body = models.TextField()
    language = models.CharField(max_length=2, choices=User.Language.choices)
    target_age_range = models.CharField(max_length=20, blank=True, help_text="e.g. '6-9'")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} ({self.language})"

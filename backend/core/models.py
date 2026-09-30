from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """Append-only record of privileged writes -- in particular every write
    a platform_admin makes into a school's data (the only role allowed to
    cross tenants). Written by `core.audit.audit()`."""

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="+"
    )
    actor_role = models.CharField(max_length=20)
    school = models.ForeignKey(
        "tenants.School", on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    action = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.actor_role}:{self.action} {self.target_type}#{self.target_id}"

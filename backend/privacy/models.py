from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class DataRequest(models.Model):
    """A data-protection request (proposal §5 privacy dashboard)."""

    class RequestType(models.TextChoices):
        EXPORT = "export", _("Export my data")
        CORRECTION = "correction", _("Correct my data")
        DELETION = "deletion", _("Delete my data")

    class Subject(models.TextChoices):
        SELF = "self", _("Myself")
        STUDENT = "student", _("A child of mine")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        IN_PROGRESS = "in_progress", _("In progress")
        COMPLETED = "completed", _("Completed")
        REJECTED = "rejected", _("Rejected")

    requested_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="data_requests")
    request_type = models.CharField(max_length=12, choices=RequestType.choices)
    subject = models.CharField(max_length=8, choices=Subject.choices)
    student = models.ForeignKey("students.Student", on_delete=models.PROTECT, null=True, blank=True, related_name="data_requests")
    school = models.ForeignKey(
        "tenants.School", on_delete=models.PROTECT, null=True, blank=True, related_name="data_requests",
        help_text="The school that handles it: the student's school, or (subject=self) the school of the requester's first linked student.",
    )
    details = models.TextField(blank=True, help_text="What to export/correct/delete, in the requester's words.")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    notes = models.TextField(blank=True, help_text="Handler's notes back to the requester.")
    handled_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    handled_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]

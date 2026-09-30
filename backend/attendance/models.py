from django.db import models
from django.utils.translation import gettext_lazy as _


class AttendanceRecord(models.Model):
    """A card tap at an attendance device. No money moves."""

    class Direction(models.TextChoices):
        IN = "in", _("In")
        OUT = "out", _("Out")

    school = models.ForeignKey("tenants.School", on_delete=models.CASCADE, related_name="attendance_records")
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="attendance_records")
    card = models.ForeignKey("cards.Card", on_delete=models.SET_NULL, null=True, blank=True, related_name="+")
    device = models.ForeignKey("pos.Device", on_delete=models.PROTECT, related_name="attendance_records")
    direction = models.CharField(max_length=3, choices=Direction.choices)
    device_local_timestamp = models.DateTimeField()
    received_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=128)

    class Meta:
        ordering = ["-device_local_timestamp", "-id"]
        constraints = [
            models.UniqueConstraint(fields=["device", "idempotency_key"], name="attendance_idempotent_per_device"),
        ]
        indexes = [models.Index(fields=["school", "device_local_timestamp"])]

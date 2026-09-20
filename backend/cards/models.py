from django.db import models


class Card(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        FROZEN = "frozen", "Frozen"
        LOST = "lost", "Lost"

    school = models.ForeignKey(
        "tenants.School", on_delete=models.CASCADE, related_name="cards"
    )
    student = models.ForeignKey(
        "students.Student", on_delete=models.CASCADE, related_name="cards"
    )
    card_uid = models.CharField(max_length=64, unique=True)
    pin_hash = models.CharField(max_length=255)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.ACTIVE)
    biometric_enrolled = models.BooleanField(
        default=False,
        help_text="Flag only; biometric capture/matching is a client (Part 3/4) concern.",
    )
    issued_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issued_at"]

    def __str__(self):
        return f"Card({self.card_uid}, {self.student}, {self.status})"

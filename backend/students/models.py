from django.conf import settings
from django.db import models


class Student(models.Model):
    school = models.ForeignKey(
        "tenants.School", on_delete=models.CASCADE, related_name="students"
    )
    name = models.CharField(max_length=255)
    class_name = models.CharField(max_length=50, help_text="e.g. 'P4', 'S2 Blue'")
    date_of_birth = models.DateField(null=True, blank=True)
    photo = models.ImageField(upload_to="students/photos/", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    guardians = models.ManyToManyField(
        settings.AUTH_USER_MODEL, through="Guardian", related_name="students"
    )

    class Meta:
        ordering = ["school", "name"]

    def __str__(self):
        return f"{self.name} ({self.school})"


class Guardian(models.Model):
    """Through-model: one or more parent Users linked to one or more
    Students (siblings share guardians; a student can have >1 guardian)."""

    class Relationship(models.TextChoices):
        MOTHER = "mother", "Mother"
        FATHER = "father", "Father"
        GUARDIAN = "guardian", "Guardian"
        OTHER = "other", "Other"

    parent = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="guardian_links"
    )
    student = models.ForeignKey(
        Student, on_delete=models.CASCADE, related_name="guardian_links"
    )
    relationship = models.CharField(
        max_length=20, choices=Relationship.choices, default=Relationship.GUARDIAN
    )
    is_primary_contact = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["parent", "student"]

    def __str__(self):
        return f"{self.parent} -> {self.student} ({self.relationship})"

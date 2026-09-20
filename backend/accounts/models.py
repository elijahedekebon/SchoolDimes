from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from django.utils.translation import gettext_lazy as _

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    """
    Custom user model shared by every role in the system. `school` is
    nullable because platform_admin users and not-yet-linked parents
    are not scoped to a single school; every other tenant-scoped model
    carries its own `school` FK derived from this user or from the
    student(s) the user is linked to -- never from client input.
    """

    class Role(models.TextChoices):
        PARENT = "parent", _("Parent")
        STUDENT = "student", _("Student")
        CANTEEN_STAFF = "canteen_staff", _("Canteen Staff")
        MERCHANT_STAFF = "merchant_staff", _("Merchant Staff")
        SCHOOL_ADMIN = "school_admin", _("School Admin")
        PLATFORM_ADMIN = "platform_admin", _("Platform Admin")

    class Language(models.TextChoices):
        ENGLISH = "en", _("English")
        LUGANDA = "lg", _("Luganda")
        KISWAHILI = "sw", _("Kiswahili")

    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(max_length=20, choices=Role.choices)
    school = models.ForeignKey(
        "tenants.School",
        on_delete=models.PROTECT,
        related_name="users",
        null=True,
        blank=True,
        help_text="Null for platform_admin and for parents not yet tied to a single school.",
    )
    preferred_language = models.CharField(
        max_length=2, choices=Language.choices, default=Language.ENGLISH
    )
    phone_number = models.CharField(max_length=20, blank=True)
    full_name = models.CharField(max_length=255, blank=True)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["role"]

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} ({self.role})"


class GuardianVerification(models.Model):
    """KYC-lite verification of a parent/guardian's identity (proposal S5)."""

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        VERIFIED = "verified", _("Verified")
        REJECTED = "rejected", _("Rejected")

    parent = models.OneToOneField(
        "accounts.User",
        on_delete=models.CASCADE,
        related_name="guardian_verification",
        limit_choices_to={"role": User.Role.PARENT},
    )
    full_name = models.CharField(max_length=255)
    id_document_type = models.CharField(
        max_length=20,
        choices=[("national_id", "National ID"), ("passport", "Passport")],
        default="national_id",
    )
    id_number = models.CharField(max_length=64)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.PENDING
    )
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"GuardianVerification({self.parent.email}, {self.status})"

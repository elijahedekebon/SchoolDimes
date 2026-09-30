from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class NotificationEvent(models.Model):
    """One notification to one user on one channel. The title/body are
    rendered once, in the recipient's preferred_language, at creation."""

    class Channel(models.TextChoices):
        IN_APP = "in_app", _("In-app")
        SMS = "sms", _("SMS")
        PUSH = "push", _("Push")

    class Status(models.TextChoices):
        PENDING = "pending", _("Pending")
        SENT = "sent", _("Sent")
        LOGGED = "logged", _("Logged (stub backend)")
        FAILED = "failed", _("Failed")

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notifications"
    )
    event_type = models.CharField(max_length=64)
    payload = models.JSONField(default=dict, blank=True)
    channel = models.CharField(max_length=10, choices=Channel.choices, default=Channel.IN_APP)
    title = models.CharField(max_length=255)
    body = models.TextField()
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error = models.CharField(max_length=255, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at", "-id"]
        indexes = [models.Index(fields=["user", "channel", "read_at"])]

    def __str__(self):
        return f"{self.event_type} -> {self.user_id} ({self.channel}, {self.status})"


class NotificationPreference(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="notification_preference"
    )
    in_app_enabled = models.BooleanField(
        default=True, help_text="In-app is the record of truth; turning it off hides nothing already stored."
    )
    sms_enabled = models.BooleanField(default=False)
    push_enabled = models.BooleanField(default=True)
    low_balance_thresholds = models.JSONField(
        default=dict,
        blank=True,
        help_text='Per-student alert level, e.g. {"12": "2000.00"}. Missing = school policy default.',
    )
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"NotificationPreference({self.user_id})"


class DevicePushToken(models.Model):
    class Platform(models.TextChoices):
        ANDROID = "android", "Android"
        IOS = "ios", "iOS"
        WEB = "web", "Web"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="push_tokens"
    )
    token = models.CharField(max_length=512, unique=True)
    platform = models.CharField(max_length=10, choices=Platform.choices)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.platform} token for {self.user_id}"

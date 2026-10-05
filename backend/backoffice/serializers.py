from django.utils.translation import gettext as _
from decimal import Decimal

from rest_framework import serializers

from core.models import AuditLog
from payments.models import UnmatchedWebhook


class OnboardAdminSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True)
    preferred_language = serializers.ChoiceField(choices=["en", "lg", "sw"], required=False)


class BrandingSerializer(serializers.Serializer):
    logo_url = serializers.URLField(required=False, allow_blank=True)
    primary_color = serializers.RegexField(r"^#[0-9a-fA-F]{6}$", required=False, allow_blank=True)


class OnboardPolicySerializer(serializers.Serializer):
    daily_spend_cap = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0"))
    weekly_spend_cap = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0"))
    per_transaction_cap = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0"))
    p2p_daily_cap = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0"))
    p2p_enabled = serializers.BooleanField(required=False, allow_null=True)
    low_balance_threshold = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, allow_null=True, min_value=Decimal("0"))


class OnboardSettingsSerializer(serializers.Serializer):
    offline_spend_ceiling = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, min_value=Decimal("0"))
    pin_lockout_threshold = serializers.IntegerField(required=False, min_value=1, max_value=20)
    device_stale_after_hours = serializers.IntegerField(required=False, min_value=1, max_value=720)
    attendance_notify_guardians = serializers.BooleanField(required=False)
    attendance_on_canteen_devices = serializers.BooleanField(required=False)


class OnboardSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    address = serializers.CharField(required=False, allow_blank=True)
    branding = BrandingSerializer(required=False)
    supported_languages = serializers.ListField(child=serializers.ChoiceField(choices=["en", "lg", "sw"]),
                                                required=False, allow_empty=False)
    policy = OnboardPolicySerializer(required=False)
    settings = OnboardSettingsSerializer(required=False)
    admin = OnboardAdminSerializer()

    def validate_admin(self, value):
        from accounts.models import User

        if User.objects.filter(email__iexact=value["email"]).exists():
            raise serializers.ValidationError({"email": [_("An account with this email already exists.")]})
        return value


class AuditLogSerializer(serializers.ModelSerializer):
    actor_email = serializers.EmailField(source="actor.email", read_only=True, default=None)
    school_name = serializers.CharField(source="school.name", read_only=True, default=None)

    class Meta:
        model = AuditLog
        fields = ["id", "actor", "actor_email", "actor_role", "school", "school_name", "action",
                  "target_type", "target_id", "details", "created_at"]


class UnmatchedWebhookSerializer(serializers.ModelSerializer):
    class Meta:
        model = UnmatchedWebhook
        fields = ["id", "reference", "aggregator_ref", "reason", "payload", "reviewed", "received_at"]
        read_only_fields = ["id", "reference", "aggregator_ref", "reason", "payload", "received_at"]

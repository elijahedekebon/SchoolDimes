from rest_framework import serializers

from .models import School, SchoolReferral


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = [
            "id",
            "name",
            "address",
            "branding",
            "supported_languages",
            "policy_defaults",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class SchoolReferralSerializer(serializers.ModelSerializer):
    class Meta:
        model = SchoolReferral
        fields = [
            "id",
            "referring_school",
            "referred_school",
            "status",
            "reward_applied",
            "created_at",
        ]
        read_only_fields = ["id", "reward_applied", "created_at"]



class SchoolSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        from .models import SchoolSettings

        model = SchoolSettings
        fields = [
            "school", "offline_spend_ceiling", "pin_lockout_threshold", "device_stale_after_hours",
            "attendance_notify_guardians", "attendance_on_canteen_devices", "updated_at",
        ]
        read_only_fields = ["school", "updated_at"]

    def validate_offline_spend_ceiling(self, value):
        if value < 0:
            raise serializers.ValidationError("Must not be negative.")
        return value

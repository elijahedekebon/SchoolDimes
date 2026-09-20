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

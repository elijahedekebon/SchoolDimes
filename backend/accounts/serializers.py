from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import GuardianVerification, User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Adds role/school/language claims to the JWT so clients (and later
    parts' permission checks) don't need an extra round-trip to /me."""

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["role"] = user.role
        token["school_id"] = user.school_id
        token["preferred_language"] = user.preferred_language
        return token


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "school",
            "preferred_language",
            "phone_number",
            "date_joined",
        ]
        read_only_fields = ["id", "role", "school", "date_joined"]


class GuardianVerificationSerializer(serializers.ModelSerializer):
    parent_email = serializers.EmailField(source="parent.email", read_only=True)

    class Meta:
        model = GuardianVerification
        fields = [
            "id",
            "parent",
            "parent_email",
            "full_name",
            "id_document_type",
            "id_number",
            "status",
            "verified_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "status", "verified_at", "created_at", "updated_at"]

    def create(self, validated_data):
        validated_data["parent"] = self.context["request"].user
        return super().create(validated_data)

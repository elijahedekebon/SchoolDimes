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
            "review_notes",
            "reviewed_by",
            "reviewed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id", "status", "verified_at", "review_notes", "reviewed_by", "reviewed_at",
            "created_at", "updated_at",
        ]

    def create(self, validated_data):
        validated_data["parent"] = self.context["request"].user
        return super().create(validated_data)


class GuardianVerificationReviewSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=["verified", "rejected"])
    review_notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class UserLookupSerializer(serializers.ModelSerializer):
    """Part 4A: the minimum an admin needs to link a guardian."""

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "role", "phone_number"]


class StaffUserSerializer(serializers.ModelSerializer):
    """Part 4A: staff accounts managed by admins."""

    password = serializers.CharField(write_only=True, min_length=8, required=False)
    merchant = serializers.IntegerField(write_only=True, required=False)
    merchant_id = serializers.IntegerField(source="merchant_link.merchant_id", read_only=True, default=None)
    merchant_name = serializers.CharField(source="merchant_link.merchant.name", read_only=True, default=None)

    class Meta:
        model = User
        fields = [
            "id", "email", "full_name", "phone_number", "role", "school", "is_active",
            "preferred_language", "date_joined", "password", "merchant", "merchant_id", "merchant_name",
        ]
        read_only_fields = ["id", "date_joined"]


class SetPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(min_length=8, write_only=True)


class RegisterSerializer(serializers.Serializer):
    """Part 4A: parent self-registration."""

    email = serializers.EmailField()
    password = serializers.CharField(min_length=8, write_only=True)
    full_name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    preferred_language = serializers.ChoiceField(choices=["en", "lg", "sw"], required=False)

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value.lower()

    def validate_password(self, value):
        from django.contrib.auth.password_validation import validate_password

        validate_password(value)
        return value

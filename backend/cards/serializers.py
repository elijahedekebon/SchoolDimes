from rest_framework import serializers

from students.models import Student

from .models import Card

PIN_REGEX = r"^\d{4,6}$"


class CardSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)  # Part 4A, additive

    class Meta:
        model = Card
        fields = [
            "id",
            "school",
            "student",
            "card_uid",
            "status",
            "biometric_enrolled",
            "issued_at",
            "updated_at",
            "student_name",
        ]
        read_only_fields = ["id", "school", "card_uid", "status", "issued_at", "updated_at"]


class CardUidField(serializers.CharField):
    """Part 4A: optional NFC UID, normalised by cards.services.normalize_card_uid."""

    def to_internal_value(self, data):
        from .services import normalize_card_uid

        value = super().to_internal_value(data)
        try:
            return normalize_card_uid(value)
        except ValueError as exc:
            raise serializers.ValidationError(str(exc))


def _uid_unused(value):
    if value and Card.objects.filter(card_uid=value).exists():
        raise serializers.ValidationError("A card with this card_uid already exists.", code="card_uid_taken")
    return value


class IssueCardSerializer(serializers.Serializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    pin = serializers.RegexField(PIN_REGEX, write_only=True)
    # Part 4A: the physical card's NFC UID; omitted -> server-generated (Part 1).
    card_uid = CardUidField(required=False, allow_blank=False, max_length=95, validators=[_uid_unused])


class ReissueCardSerializer(serializers.Serializer):
    pin = serializers.RegexField(PIN_REGEX, write_only=True)
    card_uid = CardUidField(required=False, allow_blank=False, max_length=95, validators=[_uid_unused])


class ResetPinSerializer(serializers.Serializer):
    pin = serializers.RegexField(PIN_REGEX, write_only=True)

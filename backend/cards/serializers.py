from rest_framework import serializers

from students.models import Student

from .models import Card

PIN_REGEX = r"^\d{4,6}$"


class CardSerializer(serializers.ModelSerializer):
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
        ]
        read_only_fields = ["id", "school", "card_uid", "status", "issued_at", "updated_at"]


class IssueCardSerializer(serializers.Serializer):
    student = serializers.PrimaryKeyRelatedField(queryset=Student.objects.all())
    pin = serializers.RegexField(PIN_REGEX, write_only=True)


class ReissueCardSerializer(serializers.Serializer):
    pin = serializers.RegexField(PIN_REGEX, write_only=True)

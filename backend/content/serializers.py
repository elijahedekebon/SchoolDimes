from rest_framework import serializers

from .models import FinancialLiteracyTip


class FinancialLiteracyTipSerializer(serializers.ModelSerializer):
    class Meta:
        model = FinancialLiteracyTip
        fields = [
            "id",
            "school",
            "title",
            "body",
            "language",
            "target_age_range",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

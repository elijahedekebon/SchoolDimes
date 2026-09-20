from rest_framework import serializers

from .models import Guardian, Student


class StudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Student
        fields = [
            "id",
            "school",
            "name",
            "class_name",
            "date_of_birth",
            "photo",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "school", "created_at", "updated_at"]


class GuardianSerializer(serializers.ModelSerializer):
    class Meta:
        model = Guardian
        fields = [
            "id",
            "parent",
            "student",
            "relationship",
            "is_primary_contact",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

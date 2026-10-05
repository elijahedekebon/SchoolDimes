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
    # Part 4A read-only display fields (additive).
    parent_email = serializers.EmailField(source="parent.email", read_only=True)
    parent_name = serializers.CharField(source="parent.full_name", read_only=True)
    parent_phone = serializers.CharField(source="parent.phone_number", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)
    verification_status = serializers.SerializerMethodField()

    class Meta:
        model = Guardian
        fields = [
            "id",
            "parent",
            "student",
            "relationship",
            "is_primary_contact",
            "created_at",
            "parent_email",
            "parent_name",
            "parent_phone",
            "student_name",
            "verification_status",
        ]
        read_only_fields = ["id", "created_at"]

    def get_verification_status(self, obj):
        v = getattr(obj.parent, "guardian_verification", None)
        return v.status if v else None

    def validate(self, attrs):
        # Part 4A: only parent accounts can be linked as guardians.
        parent = attrs.get("parent") or getattr(self.instance, "parent", None)
        if parent is not None and parent.role != "parent":
            raise serializers.ValidationError({"parent": ["Only parent accounts can be linked as guardians."]})
        return attrs

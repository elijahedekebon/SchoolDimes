from rest_framework import serializers

from .models import Policy, Product, ProductCategory


class ProductCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductCategory
        fields = ["id", "school", "name", "is_unhealthy", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "school", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = ["id", "school", "name", "category", "category_name", "price", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "school", "created_at", "updated_at"]

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than zero.")
        return value


class PolicySerializer(serializers.ModelSerializer):
    blocked_categories = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=ProductCategory.objects.all())
    allowed_categories = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=ProductCategory.objects.all())
    blocked_items = serializers.PrimaryKeyRelatedField(many=True, required=False, queryset=Product.objects.all())

    class Meta:
        model = Policy
        fields = [
            "id", "school", "student", "daily_spend_cap", "weekly_spend_cap", "per_transaction_cap",
            "p2p_daily_cap", "p2p_enabled", "low_balance_threshold", "blocked_categories",
            "allowed_categories", "blocked_items", "updated_by", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "school", "updated_by", "created_at", "updated_at"]
        extra_kwargs = {"student": {"required": False, "allow_null": True}}

    def validate(self, data):
        for f in ("daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "low_balance_threshold"):
            if data.get(f) is not None and data[f] < 0:
                raise serializers.ValidationError({f: "Must not be negative."})
        return data

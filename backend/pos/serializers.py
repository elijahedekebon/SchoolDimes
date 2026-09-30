from rest_framework import serializers

from .models import Device, PosTransaction, PosTransactionItem


class DeviceSerializer(serializers.ModelSerializer):
    merchant = serializers.SerializerMethodField()

    class Meta:
        model = Device
        fields = [
            "id", "school", "merchant", "device_name", "device_role", "token_prefix", "status",
            "last_seen_at", "last_sync_at", "app_version", "registered_by", "created_at", "revoked_at",
        ]
        read_only_fields = fields

    def get_merchant(self, obj):
        return getattr(obj, "merchant_id", None)


class DeviceRegisterSerializer(serializers.Serializer):
    device_name = serializers.CharField(max_length=100)
    device_role = serializers.ChoiceField(choices=Device.Role.choices)
    merchant = serializers.IntegerField(required=False, allow_null=True)
    school = serializers.IntegerField(required=False, help_text="platform_admin only")


class PosTransactionItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = PosTransactionItem
        fields = ["id", "product", "description", "category", "quantity", "unit_price", "line_total"]


class PosTransactionSerializer(serializers.ModelSerializer):
    items = PosTransactionItemSerializer(many=True, read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True, default=None)
    device_name = serializers.CharField(source="device.device_name", read_only=True)
    merchant = serializers.SerializerMethodField()
    outstanding_amount = serializers.SerializerMethodField()

    class Meta:
        model = PosTransaction
        fields = [
            "id", "device", "device_name", "school", "merchant", "card", "card_uid", "student", "student_name",
            "wallet", "channel", "amount", "applied_amount", "shortfall_amount", "recovered_amount",
            "outstanding_amount", "idempotency_key", "device_local_timestamp", "received_at", "sync_status",
            "reject_reason", "flags", "pin_verified", "ledger_reference", "review_status", "resolution",
            "reviewed_by", "reviewed_at", "review_notes", "items",
        ]
        read_only_fields = fields

    def get_merchant(self, obj):
        return getattr(obj, "merchant_id", None)

    def get_outstanding_amount(self, obj):
        if obj.resolution == PosTransaction.Resolution.WRITE_OFF:
            return "0.00"
        return str(obj.shortfall_amount - obj.recovered_amount)


class SaleItemInputSerializer(serializers.Serializer):
    product_id = serializers.IntegerField(required=False, allow_null=True)
    category_id = serializers.IntegerField(required=False, allow_null=True)
    description = serializers.CharField(max_length=255, required=False, allow_blank=True)
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)


class PurchaseSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128)
    card_uid = serializers.CharField(max_length=64)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    items = SaleItemInputSerializer(many=True, required=False)
    pin = serializers.CharField(max_length=6, required=False, allow_blank=False)
    device_local_timestamp = serializers.DateTimeField(required=False)


class PosP2PSerializer(serializers.Serializer):
    idempotency_key = serializers.CharField(max_length=128)
    sender_card_uid = serializers.CharField(max_length=64)
    pin = serializers.CharField(max_length=6)
    recipient_card_uid = serializers.CharField(max_length=64)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    note = serializers.CharField(max_length=140, required=False, allow_blank=True)


class ResolveSerializer(serializers.Serializer):
    resolution = serializers.ChoiceField(choices=PosTransaction.Resolution.choices)
    review_notes = serializers.CharField(required=False, allow_blank=True)

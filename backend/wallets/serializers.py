from rest_framework import serializers

from .models import LedgerEntry, P2PAlert, SavingsGoal, Wallet


class WalletSerializer(serializers.ModelSerializer):
    balance = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)

    class Meta:
        model = Wallet
        fields = [
            "id",
            "school",
            "student",
            "wallet_type",
            "balance",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class LedgerEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = LedgerEntry
        fields = [
            "id",
            "wallet",
            "amount",
            "direction",
            "entry_type",
            "reference_id",
            "description",
            "created_at",
        ]
        read_only_fields = fields


class SavingsGoalSerializer(serializers.ModelSerializer):
    # Part 2: progress, computed from the savings wallet's current balance.
    current_amount = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()
    is_reached = serializers.SerializerMethodField()

    class Meta:
        model = SavingsGoal
        fields = [
            "id", "wallet", "goal_name", "target_amount", "target_date", "created_at",
            "current_amount", "progress_percent", "is_reached", "reached_at",
        ]
        read_only_fields = ["id", "created_at", "reached_at"]

    def _progress(self, obj):
        from .savings import goal_progress

        return goal_progress(obj)

    def get_current_amount(self, obj):
        return str(self._progress(obj)["current_amount"])

    def get_progress_percent(self, obj):
        return self._progress(obj)["progress_percent"]

    def get_is_reached(self, obj):
        return self._progress(obj)["is_reached"]

    def validate_wallet(self, wallet):
        if wallet.wallet_type != Wallet.WalletType.SAVINGS:
            raise serializers.ValidationError("SavingsGoal.wallet must be a savings wallet.")
        return wallet


class AmountSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)


class WithdrawSerializer(AmountSerializer):
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False)


class WithdrawalWindowSerializer(serializers.Serializer):
    withdrawal_window_start = serializers.DateTimeField(allow_null=True)
    withdrawal_window_end = serializers.DateTimeField(allow_null=True)


class TransferSerializer(serializers.Serializer):
    sender_student = serializers.IntegerField()
    recipient_student = serializers.IntegerField(required=False)
    recipient_card_uid = serializers.CharField(max_length=64, required=False)
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    note = serializers.CharField(max_length=140, required=False, allow_blank=True)

    def validate(self, data):
        if not (data.get("recipient_student") or data.get("recipient_card_uid")):
            raise serializers.ValidationError("recipient_student or recipient_card_uid is required.")
        return data


class P2PTransferSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    school = serializers.IntegerField(source="school_id")
    sender_student = serializers.IntegerField(source="sender_wallet.student_id")
    sender_name = serializers.CharField(source="sender_wallet.student.name")
    recipient_student = serializers.IntegerField(source="recipient_wallet.student_id")
    recipient_name = serializers.CharField(source="recipient_wallet.student.name")
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    note = serializers.CharField()
    initiated_by = serializers.IntegerField(source="initiated_by_id", allow_null=True)
    device = serializers.IntegerField(source="device_id_ref", allow_null=True)
    created_at = serializers.DateTimeField()


class P2PAlertSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)

    class Meta:
        model = P2PAlert
        fields = ["id", "school", "student", "student_name", "rule", "details", "status",
                  "reviewed_by", "reviewed_at", "review_notes", "created_at"]
        read_only_fields = fields

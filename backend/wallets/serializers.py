from rest_framework import serializers

from .models import LedgerEntry, SavingsGoal, Wallet


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
    class Meta:
        model = SavingsGoal
        fields = ["id", "wallet", "goal_name", "target_amount", "target_date", "created_at"]
        read_only_fields = ["id", "created_at"]

    def validate_wallet(self, wallet):
        if wallet.wallet_type != Wallet.WalletType.SAVINGS:
            raise serializers.ValidationError("SavingsGoal.wallet must be a savings wallet.")
        return wallet

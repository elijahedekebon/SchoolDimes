from rest_framework import serializers

from payments.models import Channel

from .models import PooledFund, PooledFundContribution, PooledFundDisbursement
from .services import fund_totals


class PooledFundSerializer(serializers.ModelSerializer):
    total_contributed = serializers.SerializerMethodField()
    balance = serializers.SerializerMethodField()
    progress_percent = serializers.SerializerMethodField()

    class Meta:
        model = PooledFund
        fields = [
            "id", "school", "title", "purpose", "group_label", "created_by", "target_amount",
            "deadline", "status", "wallet", "total_contributed", "balance", "progress_percent",
            "created_at", "closed_at",
        ]
        read_only_fields = ["id", "created_by", "status", "wallet", "created_at", "closed_at"]
        extra_kwargs = {"school": {"required": False}}

    def _totals(self, obj):
        cache = self.context.setdefault("_totals", {})
        if obj.pk not in cache:
            cache[obj.pk] = fund_totals(obj)
        return cache[obj.pk]

    def get_total_contributed(self, obj):
        return str(self._totals(obj)["total_contributed"])

    def get_balance(self, obj):
        return str(self._totals(obj)["balance"])

    def get_progress_percent(self, obj):
        return self._totals(obj)["progress_percent"]


class ContributionSerializer(serializers.ModelSerializer):
    contributor_name = serializers.CharField(read_only=True)
    deposit_reference = serializers.CharField(source="deposit.reference", read_only=True)

    class Meta:
        model = PooledFundContribution
        fields = ["id", "contributor_user", "contributor_name", "amount", "deposit", "deposit_reference", "created_at"]


class DisbursementSerializer(serializers.ModelSerializer):
    payout_status = serializers.CharField(source="payout.status", read_only=True, default=None)

    class Meta:
        model = PooledFundDisbursement
        fields = ["id", "amount", "destination", "description", "payout", "payout_status", "disbursed_by", "created_at"]


class PooledFundDetailSerializer(PooledFundSerializer):
    total_disbursed = serializers.SerializerMethodField()
    contributions = ContributionSerializer(many=True, read_only=True)
    disbursements = DisbursementSerializer(many=True, read_only=True)

    class Meta(PooledFundSerializer.Meta):
        fields = PooledFundSerializer.Meta.fields + ["total_disbursed", "contributions", "disbursements"]

    def get_total_disbursed(self, obj):
        return str(self._totals(obj)["total_disbursed"])


class ContributeSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    channel = serializers.ChoiceField(choices=Channel.choices)
    payer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128)


class DisburseSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    destination = serializers.ChoiceField(choices=PooledFundDisbursement.Destination.choices)
    description = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128, required=False)

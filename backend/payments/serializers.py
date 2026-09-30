from django.conf import settings
from rest_framework import serializers

from .models import Channel, Deposit, GiftVoucher, Payout, RecurringTopUp, StudentTopUpLink


class ContributorInputSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=255)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    email = serializers.EmailField(required=False, allow_blank=True)
    relationship_label = serializers.CharField(max_length=64, required=False, allow_blank=True)


class DepositSerializer(serializers.ModelSerializer):
    student = serializers.IntegerField(source="wallet.student_id", read_only=True)
    contributor_name = serializers.CharField(source="contributor.name", read_only=True, default=None)

    class Meta:
        model = Deposit
        fields = [
            "id", "school", "purpose", "wallet", "student", "amount", "channel", "payer_phone",
            "status", "reference", "aggregator_ref", "instructions", "initiated_by",
            "contributor", "contributor_name", "recurring_topup", "idempotency_key",
            "failure_reason", "created_at", "confirmed_at",
        ]
        read_only_fields = fields


class PublicDepositSerializer(serializers.ModelSerializer):
    """What an unauthenticated contributor may see: no wallet/student ids."""

    class Meta:
        model = Deposit
        fields = ["reference", "amount", "channel", "status", "instructions", "failure_reason", "created_at", "confirmed_at"]
        read_only_fields = fields


class DepositCreateSerializer(serializers.Serializer):
    wallet = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    channel = serializers.ChoiceField(choices=Channel.choices)
    payer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128)


class PublicContributionSerializer(serializers.Serializer):
    contributor = ContributorInputSerializer()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    channel = serializers.ChoiceField(choices=Channel.choices)
    payer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128)


class PublicGiftVoucherSerializer(PublicContributionSerializer):
    message = serializers.CharField(max_length=280, required=False, allow_blank=True)


class GiftVoucherCreateSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    message = serializers.CharField(max_length=280, required=False, allow_blank=True)
    channel = serializers.ChoiceField(choices=Channel.choices)
    payer_phone = serializers.CharField(max_length=20, required=False, allow_blank=True)
    idempotency_key = serializers.CharField(max_length=128)


class GiftVoucherSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(read_only=True)
    deposit_reference = serializers.CharField(source="deposit.reference", read_only=True)
    deposit_status = serializers.CharField(source="deposit.status", read_only=True)
    instructions = serializers.JSONField(source="deposit.instructions", read_only=True)

    class Meta:
        model = GiftVoucher
        fields = [
            "id", "school", "student", "wallet", "amount", "message", "status", "sender_user",
            "sender_contributor", "sender_name", "deposit", "deposit_reference", "deposit_status",
            "instructions", "redeemed_at", "created_at",
        ]
        read_only_fields = fields


class PublicGiftVoucherOutSerializer(serializers.ModelSerializer):
    deposit = PublicDepositSerializer(read_only=True)

    class Meta:
        model = GiftVoucher
        fields = ["amount", "message", "status", "deposit", "created_at"]
        read_only_fields = fields


class TopUpLinkSerializer(serializers.ModelSerializer):
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = StudentTopUpLink
        fields = ["id", "student", "wallet", "token", "share_url", "active", "expires_at", "revoked_at", "created_at"]
        read_only_fields = ["id", "wallet", "token", "share_url", "active", "revoked_at", "created_at"]

    def get_share_url(self, obj):
        return f"{settings.PUBLIC_TOPUP_BASE_URL.rstrip('/')}/{obj.token}"


class RecurringTopUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = RecurringTopUp
        fields = [
            "id", "school", "parent", "student", "wallet", "amount", "channel", "payer_phone",
            "frequency", "day_of_week", "day_of_month", "next_run_at", "active", "last_run_at",
            "last_status", "consecutive_failures", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "school", "parent", "wallet", "next_run_at", "last_run_at", "last_status",
            "consecutive_failures", "created_at", "updated_at",
        ]


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            "id", "school", "purpose", "source_wallet", "amount", "phone_number", "description",
            "status", "reference", "aggregator_ref", "failure_reason", "created_at", "completed_at",
        ]
        read_only_fields = fields

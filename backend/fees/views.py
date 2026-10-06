from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.exceptions import ServiceError
from core.permissions import is_platform_admin
from policies.views import _SchoolCatalogViewSet
from students.models import Student

from . import services
from .models import FeeCategory, FeePayment


class FeeCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = FeeCategory
        fields = [
            "id", "school", "name", "amount_type", "fixed_amount", "min_amount", "max_amount",
            "active", "due_date", "applicable_classes", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "school", "created_at", "updated_at"]

    def validate(self, data):
        merged = {f: data.get(f, getattr(self.instance, f, None)) for f in
                  ("amount_type", "fixed_amount", "min_amount", "max_amount")}
        merged["amount_type"] = merged["amount_type"] or FeeCategory.AmountType.FIXED
        services.validate_category(merged)
        classes = data.get("applicable_classes")
        if classes is not None and not (isinstance(classes, list) and all(isinstance(c, str) for c in classes)):
            raise serializers.ValidationError({"applicable_classes": "Must be a list of class names."})
        return data


class FeePaymentSerializer(serializers.ModelSerializer):
    fee_category_name = serializers.CharField(source="fee_category.name", read_only=True)
    student_name = serializers.CharField(source="student.name", read_only=True)

    class Meta:
        model = FeePayment
        fields = [
            "id", "school", "student", "student_name", "fee_category", "fee_category_name", "amount",
            "paid_by", "ledger_reference", "status", "idempotency_key", "created_at",
        ]
        read_only_fields = fields


class FeeCategoryViewSet(_SchoolCatalogViewSet):
    """Read: school staff and guardians of the school's students.
    Write: that school's school_admin. ?class_name= filters applicable fees."""

    model = FeeCategory
    serializer_class = FeeCategorySerializer

    def get_queryset(self):
        return services.fee_categories_for(self.request.user, self.request.query_params)


class PayFeeSerializer(serializers.Serializer):
    student = serializers.IntegerField()
    fee_category = serializers.IntegerField()
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    idempotency_key = serializers.CharField(max_length=128, required=False)


class PayFeeView(APIView):
    def post(self, request):
        s = PayFeeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        student = Student.objects.filter(pk=d["student"]).first()
        category = FeeCategory.objects.filter(pk=d["fee_category"]).first()
        if student is None or category is None:
            raise ServiceError("not_found", _("Student or fee category not found."), status=404)
        payment, created = services.pay_fee(
            request.user, student=student, fee_category=category,
            amount=d.get("amount"), idempotency_key=d.get("idempotency_key"),
        )
        return Response(FeePaymentSerializer(payment).data, status=status.HTTP_201_CREATED if created else 200)


class FeePaymentViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """Fee payment history: guardians see their students'; school_admin their
    school's. Filters ?student=, ?fee_category=."""

    serializer_class = FeePaymentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return services.fee_payments_for(self.request.user, self.request.query_params)

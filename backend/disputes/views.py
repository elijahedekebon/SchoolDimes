from django.db.models import Q
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.permissions import is_platform_admin
from pos.services import money

from . import services
from .models import Dispute


class DisputeSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    original_amount = serializers.SerializerMethodField()
    refunded_total = serializers.SerializerMethodField()

    class Meta:
        model = Dispute
        fields = [
            "id", "school", "raised_by", "student", "student_name", "pos_transaction", "ledger_entry",
            "reason_category", "description", "status", "resolution_notes", "refund_amount",
            "original_amount", "refunded_total", "resolved_by", "resolved_at", "created_at", "updated_at",
        ]
        read_only_fields = [f for f in fields if f not in ("pos_transaction", "ledger_entry", "reason_category", "description")]

    def get_original_amount(self, obj):
        return money(services.original_amount(obj))

    def get_refunded_total(self, obj):
        return money(services.refunded_so_far(obj))


class ResolveSerializer(serializers.Serializer):
    outcome = serializers.ChoiceField(choices=["refund", "deny"])
    refund_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    resolution_notes = serializers.CharField(required=False, allow_blank=True)


class DisputeViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    """Guardians raise and follow their disputes; school_admin works the
    school's queue (?status=)."""

    serializer_class = DisputeSerializer

    def get_queryset(self):
        user = self.request.user
        qs = Dispute.objects.select_related("student", "pos_transaction", "ledger_entry")
        if is_platform_admin(user):
            pass  # read-only visibility; resolving is refused in the service
        elif user.role == User.Role.SCHOOL_ADMIN:
            qs = qs.filter(school_id=user.school_id)
        elif user.role == User.Role.PARENT:
            qs = qs.filter(Q(raised_by=user) | Q(student__guardian_links__parent=user)).distinct()
        else:
            qs = qs.none()
        for f in ("status", "student"):
            if self.request.query_params.get(f):
                qs = qs.filter(**{f: self.request.query_params[f]})
        return qs

    def create(self, request):
        s = DisputeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        dispute = services.raise_dispute(
            request.user, reason_category=d["reason_category"], description=d.get("description", ""),
            pos_transaction_id=getattr(d.get("pos_transaction"), "pk", None),
            ledger_entry_id=getattr(d.get("ledger_entry"), "pk", None),
        )
        return Response(DisputeSerializer(dispute).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        return Response(DisputeSerializer(services.start_review(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        s = ResolveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        dispute = services.resolve(request.user, self.get_object(), **s.validated_data)
        return Response(DisputeSerializer(dispute).data)

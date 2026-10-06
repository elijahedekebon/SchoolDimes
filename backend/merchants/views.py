from datetime import datetime, time, timedelta
from decimal import Decimal

from django.db.models import Q, Sum
from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.exceptions import ServiceError
from core.pagination import StandardResultsSetPagination
from core.permissions import is_platform_admin, is_school_admin
from policies.services import KAMPALA
from pos.services import money
from students.access import user_school_ids
from wallets.serializers import LedgerEntrySerializer

from . import services
from .models import Merchant, MerchantApproval


class MerchantSerializer(serializers.ModelSerializer):
    my_school_approval = serializers.SerializerMethodField()
    approved_school_ids = serializers.SerializerMethodField()

    class Meta:
        model = Merchant
        fields = ["id", "name", "category", "contact_phone", "status", "approved_school_ids",
                  "my_school_approval", "created_at", "updated_at"]
        read_only_fields = ["id", "status", "approved_school_ids", "my_school_approval", "created_at", "updated_at"]

    def get_approved_school_ids(self, obj):
        user = self.context["request"].user
        ids = services.approved_school_ids(obj) if obj.status == Merchant.Status.APPROVED else []
        if is_platform_admin(user) or services.user_merchant(user) == obj:
            return ids
        return [i for i in ids if i in user_school_ids(user)]  # never reveal other tenants

    def get_my_school_approval(self, obj):
        user = self.context["request"].user
        if not user.school_id:
            return None
        approval = obj.approvals.filter(school_id=user.school_id).first()
        return approval.status if approval else None


class MerchantViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin,
                      mixins.UpdateModelMixin, viewsets.GenericViewSet):
    """
    school_admin: sees every merchant (to find and approve ones already
      registered by a neighbouring school), approves/suspends for own school.
    parent: merchants approved for their children's schools (to block them).
    merchant_staff: their own merchant. platform_admin: everything.
    """

    serializer_class = MerchantSerializer
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_queryset(self):
        return services.merchants_for(self.request.user, self.request.query_params)

    def create(self, request):
        s = MerchantSerializer(data=request.data, context={"request": request})
        s.is_valid(raise_exception=True)
        merchant = services.create_merchant(request.user, **s.validated_data)
        return Response(MerchantSerializer(merchant, context={"request": request}).data, status=status.HTTP_201_CREATED)

    def perform_update(self, serializer):
        user = self.request.user
        merchant = serializer.instance
        if not (is_platform_admin(user) or merchant.created_by_id == user.pk):
            raise ServiceError("forbidden", _("Only the admin who registered this merchant can edit it."), status=403)
        if is_platform_admin(user) and self.request.data.get("status") in Merchant.Status.values:
            serializer.save(status=self.request.data["status"])
        else:
            serializer.save()

    def _approval(self, request, new_status):
        approval = services.set_approval(request.user, self.get_object(), new_status, request.data.get("school"))
        return Response({"merchant": approval.merchant_id, "school": approval.school_id, "status": approval.status,
                         "decided_at": approval.decided_at})

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        return self._approval(request, MerchantApproval.Status.APPROVED)

    @action(detail=True, methods=["post"])
    def suspend(self, request, pk=None):
        return self._approval(request, MerchantApproval.Status.SUSPENDED)

    @action(detail=True, methods=["post"])
    def staff(self, request, pk=None):
        user = User.objects.filter(pk=request.data.get("user")).first()
        if user is None:
            raise ServiceError("not_found", _("User not found."), status=404)
        link = services.link_staff(request.user, self.get_object(), user)
        return Response({"merchant": link.merchant_id, "user": link.user_id}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["get"])
    def statement(self, request, pk=None):
        """merchant_staff of this merchant (all its schools, ?school= to narrow)
        and school_admin (their own school only). ?from=&to= (Kampala days)."""
        merchant = self.get_object()
        user = request.user
        if is_platform_admin(user) or services.user_merchant(user) == merchant:
            school_ids = services.approved_school_ids(merchant) or list(
                merchant.approvals.values_list("school_id", flat=True))
            if request.query_params.get("school"):
                school_ids = [int(request.query_params["school"])] if int(request.query_params["school"]) in school_ids else []
        elif is_school_admin(user):
            school_ids = [user.school_id]
        else:
            raise ServiceError("not_found", _("Merchant not found."), status=404)

        def day(key, plus=0):
            value = request.query_params.get(key)
            parsed = parse_date(value) if value else None
            if value and parsed is None:
                raise ServiceError("date_invalid", _("Dates must be YYYY-MM-DD."))
            return datetime.combine(parsed + timedelta(days=plus), time.min, KAMPALA) if parsed else None

        wallets, entries = services.statement(merchant, school_ids=school_ids,
                                              date_from=day("from"), date_to=day("to", plus=1))
        credits = entries.filter(direction="credit").aggregate(s=Sum("amount"))["s"] or Decimal("0")
        debits = entries.filter(direction="debit").aggregate(s=Sum("amount"))["s"] or Decimal("0")
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(entries, request, view=self)
        return Response({
            "merchant": merchant.pk,
            "school_ids": school_ids,
            "balances": [{"school_id": w.school_id, "wallet_id": w.pk, "balance": str(w.cached_balance)} for w in wallets],
            "total_credits": money(credits),
            "total_debits": money(debits),
            "entries": {"count": paginator.page.paginator.count, "next": paginator.get_next_link(),
                        "previous": paginator.get_previous_link(),
                        "results": LedgerEntrySerializer(page, many=True).data},
        })

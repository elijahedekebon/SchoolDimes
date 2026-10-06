from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from payments.serializers import DepositSerializer

from . import services
from .serializers import (
    ContributeSerializer,
    DisbursementSerializer,
    DisburseSerializer,
    PooledFundDetailSerializer,
    PooledFundSerializer,
)


class PooledFundViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return services.funds_for(self.request.user, self.request.query_params, detail=self.action == "retrieve")

    def get_serializer_class(self):
        return PooledFundDetailSerializer if self.action == "retrieve" else PooledFundSerializer

    def create(self, request):
        s = PooledFundSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        fund = services.create_fund(
            request.user,
            title=d["title"],
            purpose=d.get("purpose", ""),
            group_label=d.get("group_label", ""),
            target_amount=d.get("target_amount"),
            deadline=d.get("deadline"),
            school_id=d["school"].pk if d.get("school") else None,
        )
        return Response(PooledFundDetailSerializer(fund).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def contribute(self, request, pk=None):
        fund = self.get_object()
        s = ContributeSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        deposit, created = services.contribute(request.user, fund, **s.validated_data)
        return Response(DepositSerializer(deposit).data, status=201 if created else 200)

    @action(detail=True, methods=["post"])
    def close(self, request, pk=None):
        fund = services.close_fund(request.user, self.get_object())
        return Response(PooledFundDetailSerializer(fund).data)

    @action(detail=True, methods=["post"])
    def disburse(self, request, pk=None):
        fund = self.get_object()
        s = DisburseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        disbursement = services.disburse(request.user, fund, **s.validated_data)
        return Response(DisbursementSerializer(disbursement).data, status=status.HTTP_201_CREATED)

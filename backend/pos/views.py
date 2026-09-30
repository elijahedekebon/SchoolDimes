from django.utils.dateparse import parse_datetime
from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ServiceError
from core.permissions import is_platform_admin, is_school_admin
from tenants.models import School
from wallets.serializers import P2PTransferSerializer

from . import services
from .authentication import DeviceTokenAuthentication, IsDevice
from .models import Device, PosTransaction
from .serializers import (
    DeviceRegisterSerializer,
    DeviceSerializer,
    PosP2PSerializer,
    PosTransactionSerializer,
    PurchaseSerializer,
    ResolveSerializer,
)


class IsSchoolAdminOrPlatformAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return is_school_admin(request.user) or is_platform_admin(request.user)


def _admin_scope(qs, user):
    return qs if is_platform_admin(user) else qs.filter(school_id=user.school_id)


# ---------------------------------------------------------------------------
# Device management (JWT, school_admin)
# ---------------------------------------------------------------------------

class DeviceViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DeviceSerializer
    permission_classes = [IsSchoolAdminOrPlatformAdmin]

    def get_queryset(self):
        user = self.request.user
        params = self.request.query_params
        if params.get("stale") == "true":
            if is_platform_admin(user) and not params.get("school"):
                raise ServiceError("school_required", _("platform_admin must pass ?school=<id>."))
            school_id = params.get("school") if is_platform_admin(user) else user.school_id
            return services.stale_devices(int(school_id))
        qs = _admin_scope(Device.objects.all(), user)
        for f in ("device_role", "status"):
            if params.get(f):
                qs = qs.filter(**{f: params[f]})
        return qs

    @action(detail=False, methods=["post"])
    def register(self, request):
        s = DeviceRegisterSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        user = request.user
        if is_platform_admin(user):
            school = School.objects.filter(pk=d.get("school")).first()
            if school is None:
                raise ServiceError("school_required", _("platform_admin must pass school."))
        else:
            school = user.school
        merchant = None
        if d.get("merchant"):
            from merchants.models import Merchant

            merchant = Merchant.objects.filter(pk=d["merchant"]).first()
            if merchant is None:
                raise ServiceError("merchant_not_approved", _("That merchant is not approved for this school."))
        device, raw_token = services.register_device(
            user, school=school, device_name=d["device_name"], device_role=d["device_role"], merchant=merchant
        )
        # The raw token is returned ONCE; only its hash is stored.
        return Response({**DeviceSerializer(device).data, "device_token": raw_token}, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        return Response(DeviceSerializer(services.revoke_device(request.user, self.get_object())).data)

    @action(detail=True, methods=["post"], url_path="rotate-token")
    def rotate_token(self, request, pk=None):
        device, raw_token = services.rotate_device_token(request.user, self.get_object())
        return Response({**DeviceSerializer(device).data, "device_token": raw_token})


# ---------------------------------------------------------------------------
# Device-token endpoints
# ---------------------------------------------------------------------------

class _DeviceView(APIView):
    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [IsDevice]
    device_roles = (Device.Role.CANTEEN, Device.Role.MERCHANT)

    @property
    def device(self):
        return self.request.user.device


class PosCacheView(_DeviceView):
    def get(self, request):
        since = None
        if request.query_params.get("since"):
            since = parse_datetime(request.query_params["since"])
            if since is None:
                raise ServiceError("since_invalid", _("since must be an ISO-8601 timestamp."))
        return Response(services.build_cache(self.device, since=since))


class PosSyncView(_DeviceView):
    def post(self, request):
        transactions = request.data.get("transactions")
        if not isinstance(transactions, list):
            raise ServiceError("transactions_required", _("transactions must be a list."))
        pin_failures = request.data.get("pin_failures") or []
        if not isinstance(pin_failures, list):
            pin_failures = []
        return Response(services.sync_batch(self.device, transactions, pin_failures))


class PosPurchaseView(_DeviceView):
    """Online sale: authorize_debit() enforced in real time."""

    def post(self, request):
        s = PurchaseSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = dict(s.validated_data)
        raw = {**request.data, "idempotency_key": d["idempotency_key"], "card_uid": d["card_uid"], "amount": str(d["amount"])}
        raw["device_local_timestamp"] = d.get("device_local_timestamp")
        result = services.record_sale(self.device, raw, channel=PosTransaction.Channel.ONLINE, pin=d.get("pin"))
        balances = services.card_balances(self.device, {d["card_uid"]})
        body = {**result, "balance": balances[0] if balances else None}
        if result["status"] == "rejected":
            return Response({**body, "code": result["reason"], "detail": result["reason"]}, status=422)
        return Response(body, status=200 if result["status"] == "duplicate" else 201)


class PosP2PView(_DeviceView):
    device_roles = (Device.Role.CANTEEN,)

    def post(self, request):
        s = PosP2PSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        transfer = services.pos_p2p_transfer(self.device, **s.validated_data)
        return Response(P2PTransferSerializer(transfer).data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Review queue (JWT, school_admin)
# ---------------------------------------------------------------------------

class PosTransactionViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """GET /pos/transactions/ -- all POS sales of the school (admin view)."""

    serializer_class = PosTransactionSerializer
    permission_classes = [IsSchoolAdminOrPlatformAdmin]

    def get_queryset(self):
        qs = _admin_scope(PosTransaction.objects.select_related("device", "student").prefetch_related("items"),
                          self.request.user)
        params = self.request.query_params
        for f in ("device", "student", "sync_status", "review_status"):
            if params.get(f):
                qs = qs.filter(**{f: params[f]})
        return qs


class ShortfallViewSet(PosTransactionViewSet):
    """GET /pos/shortfalls/ -- the review queue: shortfalls and flagged sales
    awaiting a decision (?type=shortfall|flagged, ?review_status=... to see
    recovering/resolved ones). POST /pos/shortfalls/{id}/resolve/."""

    def get_queryset(self):
        qs = super().get_queryset()
        if not self.request.query_params.get("review_status"):
            qs = qs.filter(review_status=PosTransaction.ReviewStatus.PENDING) if self.action == "list" else qs.exclude(
                review_status=PosTransaction.ReviewStatus.NONE)
        kind = self.request.query_params.get("type")
        if kind == "shortfall":
            qs = qs.filter(shortfall_amount__gt=0)
        elif kind == "flagged":
            qs = qs.filter(shortfall_amount=0)
        return qs

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        s = ResolveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        txn = services.resolve_review(request.user, self.get_object(), s.validated_data["resolution"],
                                      s.validated_data.get("review_notes", ""))
        return Response(PosTransactionSerializer(txn).data)

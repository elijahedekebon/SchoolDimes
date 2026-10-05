from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.exceptions import ServiceError
from core.money import validate_amount
from core.permissions import is_platform_admin, is_parent
from students.access import is_guardian
from students.models import Student
from wallets.models import Wallet
from wallets.services import get_student_wallet

from . import services
from .aggregator_client import get_aggregator_client
from .models import Deposit, GiftVoucher, RecurringTopUp, StudentTopUpLink
from .serializers import (
    DepositCreateSerializer,
    DepositSerializer,
    GiftVoucherCreateSerializer,
    GiftVoucherSerializer,
    PublicContributionSerializer,
    PublicDepositSerializer,
    PublicGiftVoucherOutSerializer,
    PublicGiftVoucherSerializer,
    RecurringTopUpSerializer,
    TopUpLinkSerializer,
)
from .throttles import PublicTopUpThrottle


class IsParent(permissions.BasePermission):
    message = "Only parents may perform this action."

    def has_permission(self, request, view):
        return is_parent(request.user)


def _scope_by_school_or_guardian(qs, user, student_field):
    if is_platform_admin(user):
        return qs
    if user.role == User.Role.PARENT:
        return qs.filter(**{f"{student_field}__guardian_links__parent": user}).distinct()
    if user.role == User.Role.SCHOOL_ADMIN:
        return qs.filter(school_id=user.school_id)
    return qs.none()


class DepositViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = DepositSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsParent()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = Deposit.objects.select_related("wallet", "contributor")
        if is_platform_admin(user):
            if self.request.query_params.get("school"):  # Part 4A support filter
                qs = qs.filter(school_id=self.request.query_params["school"])
        elif user.role == User.Role.PARENT:
            qs = qs.filter(Q(wallet__student__guardian_links__parent=user) | Q(initiated_by=user)).distinct()
        elif user.role == User.Role.SCHOOL_ADMIN:
            qs = qs.filter(school_id=user.school_id)
        else:
            qs = qs.none()
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(wallet__student_id=params["student"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("purpose"):
            qs = qs.filter(purpose=params["purpose"])
        return qs

    def create(self, request):
        s = DepositCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        wallet = Wallet.objects.filter(pk=data["wallet"]).select_related("student").first()
        if wallet is None:
            raise ServiceError("not_found", _("Wallet not found."), status=404)
        deposit, created = services.create_parent_deposit(
            request.user,
            wallet=wallet,
            amount=data["amount"],
            channel=data["channel"],
            payer_phone=data.get("payer_phone", ""),
            idempotency_key=data["idempotency_key"],
        )
        return Response(
            DepositSerializer(deposit).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class TopUpLinkViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = TopUpLinkSerializer
    permission_classes = [IsParent]

    def get_queryset(self):
        return StudentTopUpLink.objects.filter(
            student__guardian_links__parent=self.request.user
        ).distinct()

    def create(self, request):
        s = TopUpLinkSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        link = services.create_topup_link(
            request.user, s.validated_data["student"], s.validated_data.get("expires_at")
        )
        return Response(TopUpLinkSerializer(link).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def revoke(self, request, pk=None):
        return Response(TopUpLinkSerializer(services.revoke_topup_link(self.get_object())).data)


class GiftVoucherViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = GiftVoucherSerializer

    def get_permissions(self):
        if self.action == "create":
            return [IsParent()]
        return [permissions.IsAuthenticated()]

    def get_queryset(self):
        user = self.request.user
        qs = GiftVoucher.objects.select_related("deposit", "sender_user", "sender_contributor")
        if user.role == User.Role.PARENT:
            return qs.filter(Q(student__guardian_links__parent=user) | Q(sender_user=user)).distinct()
        return _scope_by_school_or_guardian(qs, user, "student")

    def create(self, request):
        s = GiftVoucherCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        student = Student.objects.filter(pk=data["student"]).first()
        if student is None or not is_guardian(request.user, student):
            raise ServiceError("not_found", _("Student not found."), status=404)
        voucher, created = services.create_gift_voucher(
            student=student,
            amount=data["amount"],
            message=data.get("message", ""),
            channel=data["channel"],
            payer_phone=data.get("payer_phone") or request.user.phone_number,
            idempotency_key=data["idempotency_key"],
            sender_user=request.user,
        )
        return Response(
            GiftVoucherSerializer(voucher).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class RecurringTopUpViewSet(viewsets.ModelViewSet):
    serializer_class = RecurringTopUpSerializer

    def get_permissions(self):
        if self.action in ("list", "retrieve"):
            return [permissions.IsAuthenticated()]
        return [IsParent()]

    def get_queryset(self):
        user = self.request.user
        qs = RecurringTopUp.objects.all()
        if user.role == User.Role.PARENT:
            return qs.filter(parent=user)
        return _scope_by_school_or_guardian(qs, user, "student")

    def _validated(self, serializer, instance=None):
        data = serializer.validated_data
        get = lambda f: data.get(f, getattr(instance, f, None))  # noqa: E731
        student = get("student")
        if not is_guardian(self.request.user, student):
            raise ServiceError("not_found", _("Student not found."), status=404)
        validate_amount(get("amount"))
        services.validate_schedule(get("frequency"), get("day_of_week"), get("day_of_month"))
        if not get("payer_phone"):
            raise ServiceError("phone_number_required", _("A mobile money phone number is required."))
        schedule_changed = instance is None or any(
            f in data for f in ("frequency", "day_of_week", "day_of_month")
        ) or (data.get("active") and not instance.active)
        extra = {"school_id": student.school_id, "wallet": get_student_wallet(student)}
        if schedule_changed:
            extra["next_run_at"] = services.compute_next_run(
                get("frequency"), get("day_of_week"), get("day_of_month"), timezone.now()
            )
        if data.get("active") and instance is not None and not instance.active:
            extra["consecutive_failures"] = 0
        return extra

    def perform_create(self, serializer):
        serializer.save(parent=self.request.user, **self._validated(serializer))

    def perform_update(self, serializer):
        serializer.save(**self._validated(serializer, serializer.instance))


class PaymentWebhookView(APIView):
    """POST /api/v1/payments/webhook/ -- called by the aggregator only."""

    authentication_classes = []
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        client = get_aggregator_client()
        raw = request.body
        if not client.verify_webhook_signature(raw, request.headers):
            return Response({"code": "bad_signature", "detail": "Invalid signature."}, status=401)
        try:
            event = client.parse_webhook(raw)
        except (ValueError, TypeError, ArithmeticError):
            return Response({"code": "bad_payload", "detail": "Unparseable payload."}, status=400)
        outcome = services.process_payment_event(event)
        return Response({"status": outcome})


# ---------------------------------------------------------------------------
# Public (unauthenticated) contributor endpoints, keyed by the link token
# ---------------------------------------------------------------------------

class _PublicView(APIView):
    authentication_classes = []
    permission_classes = [permissions.AllowAny]
    throttle_classes = [PublicTopUpThrottle]

    def get_link(self, token):
        link = services.resolve_topup_link(token)
        if link is None:
            raise ServiceError("not_found", _("This top-up link is invalid or no longer active."), status=404)
        return link


class PublicTopUpLinkView(_PublicView):
    def get(self, request, token):
        link = self.get_link(token)
        # ONLY these two fields -- never balances, history, ids or other PII.
        return Response({
            "student_first_name": link.student.name.split()[0] if link.student.name else "",
            "school_name": link.school.name,
        })


class PublicTopUpDepositView(_PublicView):
    def post(self, request, token):
        link = self.get_link(token)
        s = PublicContributionSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        deposit, created = services.create_contributor_deposit(
            link,
            contributor_data=data["contributor"],
            amount=data["amount"],
            channel=data["channel"],
            payer_phone=data.get("payer_phone", ""),
            idempotency_key=data["idempotency_key"],
        )
        return Response(PublicDepositSerializer(deposit).data, status=201 if created else 200)


class PublicTopUpDepositStatusView(_PublicView):
    def get(self, request, token, reference):
        link = self.get_link(token)
        deposit = get_object_or_404(Deposit, reference=reference, wallet=link.wallet, contributor__isnull=False)
        return Response(PublicDepositSerializer(deposit).data)


class PublicGiftVoucherView(_PublicView):
    def post(self, request, token):
        link = self.get_link(token)
        s = PublicGiftVoucherSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        data = s.validated_data
        replay = services.replayed_public_deposit(link, data["idempotency_key"], Deposit.Purpose.GIFT_VOUCHER)
        if replay is not None:
            return Response(PublicGiftVoucherOutSerializer(replay.gift_voucher).data, status=200)
        contributor = services.create_contributor(data["contributor"])
        voucher, created = services.create_gift_voucher(
            student=link.student,
            amount=data["amount"],
            message=data.get("message", ""),
            channel=data["channel"],
            payer_phone=data.get("payer_phone") or contributor.phone_number,
            idempotency_key=data["idempotency_key"],
            sender_contributor=contributor,
        )
        return Response(PublicGiftVoucherOutSerializer(voucher).data, status=201 if created else 200)

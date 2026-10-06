from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.pagination import StandardResultsSetPagination
from core.exceptions import ServiceError
from core.permissions import is_platform_admin, is_school_admin
from students.access import is_guardian

from . import p2p, savings
from .models import LedgerEntry, P2PAlert, SavingsGoal, Wallet
from .serializers import (
    AmountSerializer,
    LedgerEntrySerializer,
    P2PAlertSerializer,
    P2PTransferSerializer,
    SavingsGoalSerializer,
    TransferSerializer,
    WalletSerializer,
    WithdrawalWindowSerializer,
    WithdrawSerializer,
)
from .services import get_student_wallet


def wallets_visible_to(user):
    from .services import wallets_visible_to as visible

    return visible(user)


class WalletViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .services import wallets_for

        return wallets_for(self.request.user, self.request.query_params)

    @action(detail=True, methods=["get"])
    def balance(self, request, pk=None):
        wallet = self.get_object()
        entries = wallet.ledger_entries.all()
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(entries, request, view=self)
        return Response(
            {
                "wallet": WalletSerializer(wallet).data,
                "balance": wallet.balance,
                "history": {
                    "count": paginator.page.paginator.count,
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": LedgerEntrySerializer(page, many=True).data,
                },
            }
        )


    # ---- Part 2: savings operations ------------------------------------
    # {id} may be the student's main OR savings wallet; the operation always
    # acts on that student's pair.

    def _student_for_savings(self, request):
        wallet = self.get_object()
        if wallet.is_system or not savings.can_operate_savings(request.user, wallet.student):
            raise ServiceError("not_found", _("Wallet not found."), status=404)
        return wallet.student

    def _pair(self, student):
        return {
            "main": WalletSerializer(get_student_wallet(student, Wallet.WalletType.MAIN)).data,
            "savings": WalletSerializer(get_student_wallet(student, Wallet.WalletType.SAVINGS)).data,
        }

    @action(detail=True, methods=["post"], url_path="savings/move-in")
    def savings_move_in(self, request, pk=None):
        student = self._student_for_savings(request)
        s = AmountSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        savings.move_to_savings(student, s.validated_data["amount"])
        return Response(self._pair(student))

    @action(detail=True, methods=["post"], url_path="savings/move-out")
    def savings_move_out(self, request, pk=None):
        student = self._student_for_savings(request)
        s = AmountSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        savings.move_from_savings(student, s.validated_data["amount"])
        return Response(self._pair(student))

    @action(detail=True, methods=["get", "put"], url_path="savings/withdrawal-window")
    def savings_withdrawal_window(self, request, pk=None):
        student = self._student_for_savings(request)
        wallet = get_student_wallet(student, Wallet.WalletType.SAVINGS)
        if request.method == "PUT":
            if not is_guardian(request.user, student):
                raise ServiceError("forbidden", _("Only a guardian can set the withdrawal window."), status=403)
            s = WithdrawalWindowSerializer(data=request.data)
            s.is_valid(raise_exception=True)
            wallet = savings.set_withdrawal_window(
                student, s.validated_data["withdrawal_window_start"], s.validated_data["withdrawal_window_end"]
            )
        return Response({
            "wallet": wallet.pk,
            "withdrawal_window_start": wallet.withdrawal_window_start,
            "withdrawal_window_end": wallet.withdrawal_window_end,
            "is_open": savings.window_is_open(wallet),
        })

    @action(detail=True, methods=["post"], url_path="savings/withdraw")
    def savings_withdraw(self, request, pk=None):
        from payments.serializers import PayoutSerializer

        student = self._student_for_savings(request)
        s = WithdrawSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        payout = savings.withdraw_savings(
            request.user, student,
            amount=s.validated_data["amount"],
            phone_number=s.validated_data.get("phone_number", ""),
            idempotency_key=s.validated_data.get("idempotency_key"),
        )
        return Response(PayoutSerializer(payout).data, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="transfer")
    def transfer(self, request):
        """A guardian of the SENDER initiates a same-school P2P transfer."""
        from cards.models import Card
        from students.models import Student

        s = TransferSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        sender = Student.objects.filter(pk=d["sender_student"]).first()
        if sender is None or not is_guardian(request.user, sender):
            raise ServiceError("not_found", _("Student not found."), status=404)
        if d.get("recipient_card_uid"):
            card = Card.objects.filter(card_uid=d["recipient_card_uid"], school_id=sender.school_id).first()
            recipient = card.student if card else None
        else:
            recipient = Student.objects.filter(pk=d["recipient_student"], school_id=sender.school_id).first()
        if recipient is None:
            raise ServiceError("recipient_not_found", _("No such student at this school."), status=404)
        transfer = p2p.p2p_transfer(sender, recipient, d["amount"], initiated_by=request.user, note=d.get("note", ""))
        return Response(P2PTransferSerializer(transfer).data, status=status.HTTP_201_CREATED)


class P2PAlertViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """school_admin review queue for P2P pattern alerts."""

    serializer_class = P2PAlertSerializer

    def get_queryset(self):
        return p2p.alerts_for(self.request.user, self.request.query_params)

    @action(detail=True, methods=["post"])
    def review(self, request, pk=None):
        alert = p2p.review_alert(
            request.user, self.get_object(), request.data.get("status"), request.data.get("review_notes", "")
        )
        return Response(P2PAlertSerializer(alert).data)


class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        from .services import goals_for

        return goals_for(self.request.user, self.request.query_params)

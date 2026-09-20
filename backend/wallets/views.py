from rest_framework import mixins, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.pagination import StandardResultsSetPagination
from core.permissions import is_platform_admin

from .models import LedgerEntry, SavingsGoal, Wallet
from .serializers import LedgerEntrySerializer, SavingsGoalSerializer, WalletSerializer


def wallets_visible_to(user):
    qs = Wallet.objects.select_related("student", "school")
    if is_platform_admin(user):
        return qs
    if user.role == User.Role.PARENT:
        return qs.filter(student__guardian_links__parent=user).distinct()
    return qs.filter(school_id=user.school_id)


class WalletViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return wallets_visible_to(self.request.user)

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


class SavingsGoalViewSet(viewsets.ModelViewSet):
    serializer_class = SavingsGoalSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SavingsGoal.objects.filter(
            wallet__in=wallets_visible_to(self.request.user)
        ).select_related("wallet")

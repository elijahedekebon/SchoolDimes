from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.permissions import IsSchoolAdminOrPlatformAdmin, is_platform_admin, is_school_admin

from .models import Card
from .serializers import CardSerializer, IssueCardSerializer, ReissueCardSerializer
from .services import freeze_card, issue_card, reissue_card, unfreeze_card


def can_manage_card(user, card: Card) -> bool:
    """Generic freeze/unfreeze authorization, reused by later parts:
    platform_admin, the card's own school_admin, or a parent linked to
    the card's student via a Guardian row."""
    if is_platform_admin(user):
        return True
    if is_school_admin(user):
        return card.school_id == user.school_id
    if user.role == User.Role.PARENT:
        return card.student.guardian_links.filter(parent=user).exists()
    return False


class CardViewSet(viewsets.ModelViewSet):
    serializer_class = CardSerializer
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        user = self.request.user
        qs = Card.objects.select_related("student", "school")
        if is_platform_admin(user):
            return qs
        if user.role == User.Role.PARENT:
            return qs.filter(student__guardian_links__parent=user).distinct()
        return qs.filter(school_id=user.school_id)

    def get_permissions(self):
        if self.action in ("issue", "reissue"):
            return [IsSchoolAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated()]

    @action(detail=False, methods=["post"])
    def issue(self, request):
        serializer = IssueCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        student = serializer.validated_data["student"]
        if not is_platform_admin(request.user) and student.school_id != request.user.school_id:
            return Response(
                {"detail": "Cannot issue a card for a student outside your school."},
                status=status.HTTP_403_FORBIDDEN,
            )
        card = issue_card(student, serializer.validated_data["pin"])
        return Response(CardSerializer(card).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reissue(self, request, pk=None):
        old_card = self.get_object()
        if not is_platform_admin(request.user) and old_card.school_id != request.user.school_id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ReissueCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_card = reissue_card(old_card, serializer.validated_data["pin"])
        return Response(CardSerializer(new_card).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def freeze(self, request, pk=None):
        card = self.get_object()
        if not can_manage_card(request.user, card):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(CardSerializer(freeze_card(card)).data)

    @action(detail=True, methods=["post"])
    def unfreeze(self, request, pk=None):
        card = self.get_object()
        if not can_manage_card(request.user, card):
            return Response(status=status.HTTP_403_FORBIDDEN)
        return Response(CardSerializer(unfreeze_card(card)).data)

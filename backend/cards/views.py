from django.utils.translation import gettext as _
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.permissions import IsSchoolAdminOrPlatformAdmin, is_platform_admin, is_school_admin

from .models import Card
from .serializers import CardSerializer, IssueCardSerializer, ReissueCardSerializer, ResetPinSerializer
from .services import (
    card_status_changed,
    freeze_card,
    issue_card,
    reissue_card,
    report_lost_card,
    reset_card_pin,
    unfreeze_card,
)


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
        # Part 4A list filters: ?student=, ?status=, ?card_uid= (normalised).
        params = self.request.query_params
        if params.get("student"):
            qs = qs.filter(student_id=params["student"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])
        if params.get("card_uid"):
            from .services import normalize_card_uid

            try:
                qs = qs.filter(card_uid=normalize_card_uid(params["card_uid"]))
            except ValueError:
                qs = qs.none()
        if is_platform_admin(user):
            return qs.filter(school_id=params["school"]) if params.get("school") else qs
        if user.role == User.Role.PARENT:
            return qs.filter(student__guardian_links__parent=user).distinct()
        return qs.filter(school_id=user.school_id)

    def get_permissions(self):
        if self.action in ("issue", "reissue", "reset_pin"):
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
        card = issue_card(student, serializer.validated_data["pin"],
                          card_uid=serializer.validated_data.get("card_uid"))
        return Response(CardSerializer(card).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def reissue(self, request, pk=None):
        old_card = self.get_object()
        if not is_platform_admin(request.user) and old_card.school_id != request.user.school_id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        serializer = ReissueCardSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        new_card = reissue_card(old_card, serializer.validated_data["pin"],
                                card_uid=serializer.validated_data.get("card_uid"))
        return Response(CardSerializer(new_card).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def freeze(self, request, pk=None):
        card = self.get_object()
        if not can_manage_card(request.user, card):
            return Response(status=status.HTTP_403_FORBIDDEN)
        # Part 2: same response; also notifies the other guardians and is
        # audit-logged for platform_admin. Takes effect for authorize_debit()
        # immediately and reaches offline POS devices on their next cache refresh.
        freeze_card(card)
        card_status_changed(card, request.user, "card_frozen")
        return Response(CardSerializer(card).data)

    @action(detail=True, methods=["post"])
    def unfreeze(self, request, pk=None):
        card = self.get_object()
        if not can_manage_card(request.user, card):
            return Response(status=status.HTTP_403_FORBIDDEN)
        if card.status == Card.Status.LOST:
            # Part 2: a lost card is replaced via reissue, never reactivated.
            return Response(
                {"code": "card_lost", "detail": _("A lost card cannot be unfrozen; reissue it instead.")},
                status=status.HTTP_409_CONFLICT,
            )
        unfreeze_card(card)
        card_status_changed(card, request.user, "card_unfrozen")
        return Response(CardSerializer(card).data)

    @action(detail=True, methods=["post"], url_path="report-lost")
    def report_lost(self, request, pk=None):
        """Part 2: guardian or school_admin marks the card lost (permanent).
        A school_admin then issues a replacement via POST /cards/{id}/reissue/."""
        card = self.get_object()
        if not can_manage_card(request.user, card):
            return Response(status=status.HTTP_403_FORBIDDEN)
        report_lost_card(card)
        card_status_changed(card, request.user, "card_reported_lost")
        return Response(CardSerializer(card).data)

    @action(detail=True, methods=["post"], url_path="reset-pin")
    def reset_pin(self, request, pk=None):
        """Part 4A: school_admin (own school) / platform_admin (audit-logged)
        sets a new 4-6 digit PIN. Response: the Card (never the hash)."""
        from core.audit import audit

        card = self.get_object()
        if not is_platform_admin(request.user) and card.school_id != request.user.school_id:
            return Response(status=status.HTTP_403_FORBIDDEN)
        if card.status == Card.Status.LOST:
            return Response(
                {"code": "card_lost", "detail": _("A lost card can't get a new PIN; reissue it instead.")},
                status=status.HTTP_409_CONFLICT,
            )
        s = ResetPinSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        reset_card_pin(card, s.validated_data["pin"])
        audit(request.user, "card.reset_pin", card)
        return Response(CardSerializer(card).data)

from rest_framework import permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from accounts.models import User
from core.permissions import (
    IsSameSchoolObject,
    IsSchoolAdminOrPlatformAdmin,
    is_platform_admin,
)

from wallets.services import ensure_student_wallets

from .models import Guardian, Student
from .serializers import GuardianSerializer, StudentSerializer


from django.db.models import F as models_F  # noqa: E402


def filter_students(qs, params):
    """Part 4A list filters: ?search= (name or class, case-insensitive),
    ?class_name= (exact), ?card_status=active|frozen|lost|none (current card),
    ?low_balance=true (main wallet below the student's effective
    low_balance_threshold)."""
    from django.db.models import Q

    search = (params.get("search") or "").strip()
    if search:
        qs = qs.filter(Q(name__icontains=search) | Q(class_name__icontains=search))
    if params.get("class_name"):
        qs = qs.filter(class_name__iexact=params["class_name"])
    card_status = params.get("card_status")
    if card_status in ("active", "frozen"):
        qs = qs.filter(cards__status=card_status).distinct()
    elif card_status == "lost":  # every card lost: needs a replacement
        qs = qs.filter(cards__isnull=False).exclude(cards__status__in=["active", "frozen"]).distinct()
    elif card_status == "none":
        qs = qs.filter(cards__isnull=True)
    if params.get("low_balance") == "true":
        qs = _low_balance(qs)
    return qs


def _low_balance(qs):
    """Main wallet below the school default's low_balance_threshold (or
    LOW_BALANCE_DEFAULT_THRESHOLD). Per-student overrides are not applied here;
    this is a list filter, the exact per-guardian rule lives in notifications."""
    from decimal import Decimal

    from django.conf import settings
    from django.db.models import DecimalField, OuterRef, Subquery, Value
    from django.db.models.functions import Coalesce

    from policies.models import Policy
    from wallets.models import Wallet

    default_threshold = Policy.objects.filter(school_id=OuterRef("school_id"), student=None).values("low_balance_threshold")[:1]
    main_balance = Wallet.objects.filter(student=OuterRef("pk"), wallet_type="main").values("cached_balance")[:1]
    return qs.annotate(
        _threshold=Coalesce(Subquery(default_threshold), Value(Decimal(settings.LOW_BALANCE_DEFAULT_THRESHOLD)),
                            output_field=DecimalField(max_digits=12, decimal_places=2)),
        _main_balance=Subquery(main_balance, output_field=DecimalField(max_digits=12, decimal_places=2)),
    ).filter(_main_balance__lt=models_F("_threshold"))


class StudentViewSet(viewsets.ModelViewSet):
    serializer_class = StudentSerializer
    permission_classes = [permissions.IsAuthenticated, IsSameSchoolObject]

    def get_queryset(self):
        user = self.request.user
        qs = Student.objects.select_related("school")
        if is_platform_admin(user):
            school_id = self.request.query_params.get("school")
            qs = qs.filter(school_id=school_id) if school_id else qs
        elif user.role == User.Role.PARENT:
            qs = qs.filter(guardian_links__parent=user).distinct()
        else:
            # school_admin / canteen_staff / merchant_staff: scoped to own school
            qs = qs.filter(school_id=user.school_id)
        if self.action == "list":
            qs = filter_students(qs, self.request.query_params)
        return qs

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsSchoolAdminOrPlatformAdmin()]
        # Part 2 actions and (Part 4A, approved fix of the Part 1 quirk) every
        # read: scoping comes from get_queryset() -- parents only ever see
        # their linked students, staff their own school. IsSameSchoolObject
        # refused parents (their school is null) on GET /students/{id}/.
        return [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        user = self.request.user
        # tenant scoping is always derived server-side, never from client input,
        # except platform_admin who legitimately operates across tenants.
        if is_platform_admin(user):
            school = serializer.validated_data.get("school") or self.request.data.get("school")
            serializer.save(school_id=school if isinstance(school, int) else user.school_id)
        else:
            serializer.save(school=user.school)
        # Part 2: every student gets their main + savings wallets at onboarding.
        ensure_student_wallets(serializer.instance)

    # ---- Part 2 read-only student sub-resources -------------------------

    def _student_for_family_or_admin(self):
        from django.utils.translation import gettext as _

        from core.exceptions import ServiceError
        from students.access import can_view_student

        student = self.get_object()
        if not can_view_student(self.request.user, student):
            raise ServiceError("not_found", _("Student not found."), status=404)
        return student

    @action(detail=True, methods=["get"], url_path="p2p-history")
    def p2p_history(self, request, pk=None):
        """Guardians of the student and that school's school_admin only."""
        from django.db.models import Q

        from core.pagination import StandardResultsSetPagination
        from wallets.models import P2PTransfer
        from wallets.serializers import P2PTransferSerializer

        student = self._student_for_family_or_admin()
        qs = P2PTransfer.objects.filter(
            Q(sender_wallet__student=student) | Q(recipient_wallet__student=student)
        ).select_related("sender_wallet__student", "recipient_wallet__student")
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(P2PTransferSerializer(page, many=True).data)

    @action(detail=True, methods=["get"], url_path="effective-policy")
    def effective_policy(self, request, pk=None):
        """Anyone who can see the student (guardians, that school's staff)."""
        from policies.services import get_effective_policy

        student = self.get_object()
        return Response({"student": student.pk, **get_effective_policy(student).to_dict()})

    @action(detail=True, methods=["get"], url_path="attendance")
    def attendance(self, request, pk=None):
        """Guardians of the student and that school's school_admin.
        ?date=YYYY-MM-DD or ?from=&to= (Africa/Kampala days), ?direction=."""
        from attendance.models import AttendanceRecord
        from attendance.views import AttendanceRecordSerializer, filter_by_date
        from core.pagination import StandardResultsSetPagination

        student = self._student_for_family_or_admin()
        qs = filter_by_date(
            AttendanceRecord.objects.filter(student=student).select_related("student", "device"),
            request.query_params,
        )
        paginator = StandardResultsSetPagination()
        page = paginator.paginate_queryset(qs, request, view=self)
        return paginator.get_paginated_response(AttendanceRecordSerializer(page, many=True).data)


class GuardianViewSet(viewsets.ModelViewSet):
    serializer_class = GuardianSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = Guardian.objects.select_related("parent", "student", "parent__guardian_verification")
        # Part 4A: ?student= / ?parent= filters.
        for f in ("student", "parent"):
            if self.request.query_params.get(f):
                qs = qs.filter(**{f: self.request.query_params[f]})
        if is_platform_admin(user):
            return qs
        if user.role == User.Role.PARENT:
            return qs.filter(parent=user)
        return qs.filter(student__school_id=user.school_id)

    def get_permissions(self):
        if self.action in ("create", "update", "partial_update", "destroy"):
            return [IsSchoolAdminOrPlatformAdmin()]
        return [permissions.IsAuthenticated()]

    def _check_student_school(self, serializer):
        # Part 4A tenant fix: a school_admin may only link students of their own school.
        from core.exceptions import ServiceError

        student = serializer.validated_data.get("student")
        user = self.request.user
        if student is not None and not is_platform_admin(user) and student.school_id != user.school_id:
            raise ServiceError("not_found", "Student not found.", status=404)

    def perform_create(self, serializer):
        self._check_student_school(serializer)
        serializer.save()

    def perform_update(self, serializer):
        self._check_student_school(serializer)
        serializer.save()

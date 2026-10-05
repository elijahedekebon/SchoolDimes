from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _
from rest_framework import mixins, permissions, serializers, viewsets
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.exceptions import ServiceError
from core.permissions import is_platform_admin
from pos.authentication import DeviceTokenAuthentication, DevicePrincipal

from . import services
from .models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source="student.name", read_only=True)
    device_name = serializers.CharField(source="device.device_name", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = ["id", "school", "student", "student_name", "card", "device", "device_name", "direction",
                  "device_local_timestamp", "received_at", "idempotency_key"]
        read_only_fields = fields


class _CanRecordAttendance(permissions.BasePermission):
    message = "This device may not record attendance."

    def has_permission(self, request, view):
        return isinstance(request.user, DevicePrincipal) and services.device_may_record_attendance(request.user.device)


class AttendanceTapView(APIView):
    """POST /attendance/tap/ -- one tap object, or {"taps": [...]} (offline queue)."""

    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [_CanRecordAttendance]

    def post(self, request):
        device = request.user.device
        taps = request.data.get("taps") if isinstance(request.data, dict) and "taps" in request.data else [request.data]
        if not isinstance(taps, list):
            raise ServiceError("taps_invalid", _("taps must be a list."))
        results = services.record_taps(device, taps)
        return Response({"results": results, "created": sum(r["status"] == "created" for r in results)})


def filter_by_date(qs, params):
    for key, lookup in (("date", None), ("from", "gte"), ("to", "lt")):
        if params.get(key):
            day = parse_date(params[key])
            if day is None:
                raise ServiceError("date_invalid", _("Dates must be YYYY-MM-DD."))
            start, end = services.kampala_day_range(day)
            if key == "date":
                qs = qs.filter(device_local_timestamp__gte=start, device_local_timestamp__lt=end)
            elif key == "from":
                qs = qs.filter(device_local_timestamp__gte=start)
            else:
                qs = qs.filter(device_local_timestamp__lt=end)  # inclusive "to" day
    if params.get("direction"):
        qs = qs.filter(direction=params["direction"])
    return qs


class AttendanceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """GET /attendance/?date=YYYY-MM-DD (Africa/Kampala day) &student= &direction=
    school_admin: their school; guardians: their own children only."""

    serializer_class = AttendanceRecordSerializer

    def get_queryset(self):
        user = self.request.user
        qs = AttendanceRecord.objects.select_related("student", "device")
        if is_platform_admin(user):
            pass
        elif user.role == User.Role.SCHOOL_ADMIN:
            qs = qs.filter(school_id=user.school_id)
        elif user.role == User.Role.PARENT:
            qs = qs.filter(student__guardian_links__parent=user).distinct()
        else:
            qs = qs.none()
        if self.request.query_params.get("student"):
            qs = qs.filter(student_id=self.request.query_params["student"])
        return filter_by_date(qs, self.request.query_params)



class AttendanceRosterView(APIView):
    """Part 3 contract addition: GET /attendance/roster/?since=<ISO> -- for
    devices that record attendance. Names/photos so the gate can greet a
    student offline; no PIN hashes, balances or policies."""

    authentication_classes = [DeviceTokenAuthentication]
    permission_classes = [_CanRecordAttendance]

    def get(self, request):
        from django.utils.dateparse import parse_datetime

        since = None
        if request.query_params.get("since"):
            since = parse_datetime(request.query_params["since"])
            if since is None:
                raise ServiceError("since_invalid", _("since must be an ISO-8601 timestamp."))
        return Response(services.build_roster(request.user.device, since=since))

from django.utils import timezone
from django.utils.dateparse import parse_date
from django.utils.translation import gettext as _
from rest_framework.response import Response
from rest_framework.views import APIView

from core.exceptions import ServiceError
from core.permissions import is_platform_admin, is_school_admin
from policies.services import KAMPALA
from students.access import is_guardian
from students.models import Student
from tenants.models import School

from . import services


def _date(value, name):
    parsed = parse_date(value) if value else None
    if value and parsed is None:
        raise ServiceError("date_invalid", _("%(name)s must be YYYY-MM-DD.") % {"name": name})
    return parsed


def _range(request):
    default_from, default_to = services.default_range()
    day_from = _date(request.query_params.get("from"), "from") or default_from
    day_to = _date(request.query_params.get("to"), "to") or default_to
    if day_to < day_from or (day_to - day_from).days > 366:
        raise ServiceError("range_invalid", _("from must be before to, and the range at most a year."))
    return day_from, day_to


def _school_scope(request):
    """school_admin: their own school only. platform_admin: ?school=<id>, or
    all schools as a cross-school summary. Everyone else: 403."""
    user = request.user
    if is_school_admin(user):
        return [user.school_id], False
    if is_platform_admin(user):
        if request.query_params.get("school"):
            return [int(request.query_params["school"])], False
        return list(School.objects.values_list("pk", flat=True)), True
    raise ServiceError("forbidden", _("Analytics are for school administrators."), status=403)


class SalesSummaryView(APIView):
    def get(self, request):
        school_ids, cross = _school_scope(request)
        return Response(services.sales_summary(school_ids, *_range(request), per_school=cross))


class BestSellersView(APIView):
    def get(self, request):
        school_ids, _cross = _school_scope(request)
        limit = min(int(request.query_params.get("limit", 10)), 100)
        return Response(services.best_sellers(school_ids, *_range(request), limit=limit))


class PeakHoursView(APIView):
    def get(self, request):
        school_ids, _cross = _school_scope(request)
        return Response(services.peak_hours(school_ids, *_range(request)))


class CategoryBreakdownView(APIView):
    def get(self, request):
        school_ids, _cross = _school_scope(request)
        return Response(services.category_breakdown(school_ids, *_range(request)))


class StudentSpendingView(APIView):
    """That school's school_admin and the student's guardians only; not
    platform_admin (per-student data is never cross-tenant)."""

    def get(self, request, student_id):
        student = Student.objects.filter(pk=student_id).first()
        user = request.user
        allowed = student is not None and (
            is_guardian(user, student) or (is_school_admin(user) and user.school_id == student.school_id))
        if not allowed:
            raise ServiceError("not_found", _("Student not found."), status=404)
        return Response(services.student_spending(student, *_range(request)))


class ReconciliationView(APIView):
    def get(self, request):
        school_ids, cross = _school_scope(request)
        day = _date(request.query_params.get("date"), "date") or timezone.now().astimezone(KAMPALA).date()
        if cross:
            return Response({"date": day.isoformat(), "schools": [services.reconciliation(s, day) for s in school_ids]})
        return Response(services.reconciliation(school_ids[0], day))

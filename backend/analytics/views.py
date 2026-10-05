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


def _range(request):
    return services.date_range(request.query_params)


def _date(value, name):
    return services.parse_day(value, name)


def _school_scope(request):
    return services.school_scope(request.user, request.query_params)


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
        return Response(services.student_spending_for(request.user, student_id, request.query_params))


class ReconciliationView(APIView):
    def get(self, request):
        school_ids, cross = _school_scope(request)
        day = _date(request.query_params.get("date"), "date") or timezone.now().astimezone(KAMPALA).date()
        if cross:
            return Response({"date": day.isoformat(), "schools": [services.reconciliation(s, day) for s in school_ids]})
        return Response(services.reconciliation(school_ids[0], day))

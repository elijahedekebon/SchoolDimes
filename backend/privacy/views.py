import csv
import io

from django.db.models import Q
from django.http import HttpResponse
from django.utils.translation import gettext as _
from rest_framework import mixins, renderers, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from core.exceptions import ServiceError
from core.permissions import is_platform_admin, is_school_admin
from students.models import Student

from . import services
from .models import DataRequest


class CSVRenderer(renderers.BaseRenderer):
    """Only used so DRF's ?format=csv negotiation succeeds; the view builds
    the CSV itself."""

    media_type = "text/csv"
    format = "csv"
    charset = "utf-8"

    def render(self, data, accepted_media_type=None, renderer_context=None):
        return data if isinstance(data, (bytes, str)) else b""


class MyDataView(APIView):
    """GET /privacy/my-data/?format=json|csv -- parents only."""

    renderer_classes = [renderers.JSONRenderer, CSVRenderer]

    def get(self, request):
        if request.user.role != User.Role.PARENT:
            raise ServiceError("forbidden", _("The privacy export is for parents."), status=403)
        data = services.my_data(request.user)
        if request.accepted_renderer.format == "csv":
            buffer = io.StringIO()
            writer = csv.writer(buffer)
            for row in services.my_data_csv_rows(data):
                writer.writerow(row)
            response = HttpResponse(buffer.getvalue(), content_type="text/csv; charset=utf-8")
            response["Content-Disposition"] = 'attachment; filename="schooldimes-my-data.csv"'
            return response
        return Response(data)


class DataRequestSerializer(serializers.ModelSerializer):
    retention_notice = serializers.SerializerMethodField()

    class Meta:
        model = DataRequest
        fields = ["id", "requested_by", "request_type", "subject", "student", "school", "details", "status",
                  "notes", "handled_by", "handled_at", "created_at", "retention_notice"]
        read_only_fields = ["id", "requested_by", "school", "status", "notes", "handled_by", "handled_at",
                            "created_at", "retention_notice"]

    def get_retention_notice(self, obj):
        # shown on every deletion request so nobody is surprised by what is kept
        return str(services.RETENTION_NOTICE) if obj.request_type == DataRequest.RequestType.DELETION else None


class DataRequestViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.CreateModelMixin, viewsets.GenericViewSet):
    serializer_class = DataRequestSerializer

    def get_queryset(self):
        user = self.request.user
        qs = DataRequest.objects.all()
        # Part 4A: ?status= / ?request_type= filters for the admin queue.
        for f in ("status", "request_type"):
            if self.request.query_params.get(f):
                qs = qs.filter(**{f: self.request.query_params[f]})
        if is_platform_admin(user):
            return qs
        if is_school_admin(user):
            # requests about the school's students, or from parents of them
            return qs.filter(Q(school_id=user.school_id)
                             | Q(requested_by__guardian_links__student__school_id=user.school_id)).distinct()
        return qs.filter(requested_by=user)

    def create(self, request):
        if request.user.role != User.Role.PARENT:
            raise ServiceError("forbidden", _("Data requests are made by parents."), status=403)
        s = DataRequestSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        d = s.validated_data
        req = services.create_request(request.user, request_type=d["request_type"], subject=d["subject"],
                                      student=d.get("student"), details=d.get("details", ""))
        return Response(DataRequestSerializer(req).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def handle(self, request, pk=None):
        req = self.get_object()
        if not is_school_admin(request.user):
            raise ServiceError("forbidden", _("Only a school admin handles data requests."), status=403)
        req = services.handle_request(request.user, req, status=request.data.get("status"),
                                      notes=request.data.get("notes", ""))
        return Response(DataRequestSerializer(req).data)

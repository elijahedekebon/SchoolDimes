from decimal import Decimal, InvalidOperation

from django.utils import timezone
from rest_framework import mixins, serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.response import Response

from students.access import linked_student_ids

from .models import DevicePushToken, NotificationEvent, NotificationPreference
from . import services
from .services import get_preferences


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationEvent
        fields = ["id", "event_type", "title", "body", "payload", "channel", "status", "created_at", "sent_at", "read_at"]
        read_only_fields = fields


class NotificationViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """The caller's in-app notifications (the SMS/push copies are delivery
    records, not listed). ?unread=true, ?event_type=."""

    serializer_class = NotificationSerializer

    def get_queryset(self):
        return services.inbox(self.request.user, self.request.query_params)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response.data["unread_count"] = services.unread_count(request.user)
        return response

    @action(detail=True, methods=["post"])
    def read(self, request, pk=None):
        return Response(NotificationSerializer(services.mark_read(self.get_object())).data)

    @action(detail=False, methods=["post"], url_path="read-all")
    def read_all(self, request):
        return Response({"marked_read": services.mark_all_read(request.user, request.query_params)})


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NotificationPreference
        fields = ["in_app_enabled", "sms_enabled", "push_enabled", "low_balance_thresholds", "updated_at"]
        read_only_fields = ["updated_at"]

    def validate_low_balance_thresholds(self, value):
        if not isinstance(value, dict):
            raise serializers.ValidationError("Must be an object of {student_id: amount}.")
        allowed = {str(i) for i in linked_student_ids(self.context["request"].user)}
        clean = {}
        for student_id, amount in value.items():
            if str(student_id) not in allowed:
                raise serializers.ValidationError(f"Student {student_id} is not linked to you.")
            try:
                amount = Decimal(str(amount))
            except InvalidOperation:
                raise serializers.ValidationError("Amounts must be numbers.")
            if amount < 0:
                raise serializers.ValidationError("Amounts must not be negative.")
            clean[str(student_id)] = str(amount.quantize(Decimal("0.01")))
        return clean


class PreferenceView(RetrieveUpdateAPIView):
    serializer_class = PreferenceSerializer
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_object(self):
        return get_preferences(self.request.user)


class PushTokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = DevicePushToken
        fields = ["id", "token", "platform", "created_at", "last_used_at"]
        read_only_fields = ["id", "created_at", "last_used_at"]
        extra_kwargs = {"token": {"validators": []}}


class PushTokenViewSet(mixins.ListModelMixin, mixins.CreateModelMixin, mixins.DestroyModelMixin, viewsets.GenericViewSet):
    """Register the parent app's FCM/APNs token. POST is an upsert: a token
    seen before (e.g. a phone that changed hands) moves to the caller.
    DELETE /notifications/push-tokens/{token}/ on logout."""

    serializer_class = PushTokenSerializer
    lookup_field = "token"
    lookup_value_regex = "[^/]+"

    def get_queryset(self):
        return DevicePushToken.objects.filter(user=self.request.user)

    def create(self, request):
        s = PushTokenSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        token, created = DevicePushToken.objects.update_or_create(
            token=s.validated_data["token"],
            defaults={"user": request.user, "platform": s.validated_data["platform"]},
        )
        return Response(PushTokenSerializer(token).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

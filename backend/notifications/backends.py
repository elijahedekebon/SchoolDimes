"""
Channel backends. `in_app` is fully working: the NotificationEvent row IS
the in-app notification, read via GET /api/v1/notifications/.

SMS (Africa's Talking) and push (FCM) are STUBS: they log exactly what they
would send and mark the event `logged`. They do not pretend to deliver.
Where real credentials plug in:
  - SMS:  set SMS_BACKEND=africastalking plus AFRICASTALKING_USERNAME,
          AFRICASTALKING_API_KEY, AFRICASTALKING_SENDER_ID, then implement
          AfricasTalkingSmsBackend.send() (POST to
          https://api.africastalking.com/version1/messaging).
  - Push: set PUSH_BACKEND=fcm plus FCM_PROJECT_ID and
          FCM_SERVICE_ACCOUNT_FILE, then implement FcmPushBackend.send()
          (FCM HTTP v1: POST .../projects/{id}/messages:send per token).
"""
import logging

from django.conf import settings
from django.utils import timezone

from .models import NotificationEvent

logger = logging.getLogger("schooldimes.notifications")


class BaseBackend:
    def send(self, event: NotificationEvent) -> None:
        raise NotImplementedError


class InAppBackend(BaseBackend):
    def send(self, event):
        event.status = NotificationEvent.Status.SENT
        event.sent_at = timezone.now()
        event.save(update_fields=["status", "sent_at"])


class LoggingSmsBackend(BaseBackend):
    def send(self, event):
        phone = event.user.phone_number
        if not phone:
            event.status = NotificationEvent.Status.FAILED
            event.error = "no phone_number on user"
            event.save(update_fields=["status", "error"])
            return
        logger.info("[SMS stub] to=%s text=%s: %s", phone, event.title, event.body)
        event.status = NotificationEvent.Status.LOGGED
        event.sent_at = timezone.now()
        event.save(update_fields=["status", "sent_at"])


class AfricasTalkingSmsBackend(LoggingSmsBackend):
    # TODO(real integration): call Africa's Talking with settings.AFRICASTALKING_*.
    # Until implemented this behaves exactly like the logging stub.
    pass


class LoggingPushBackend(BaseBackend):
    def send(self, event):
        tokens = list(event.user.push_tokens.values_list("token", flat=True))
        if not tokens:
            event.status = NotificationEvent.Status.FAILED
            event.error = "no push tokens registered"
            event.save(update_fields=["status", "error"])
            return
        logger.info(
            "[Push stub] tokens=%d title=%s body=%s data=%s",
            len(tokens), event.title, event.body, event.payload,
        )
        event.status = NotificationEvent.Status.LOGGED
        event.sent_at = timezone.now()
        event.save(update_fields=["status", "sent_at"])


class FcmPushBackend(LoggingPushBackend):
    # TODO(real integration): FCM HTTP v1 with settings.FCM_PROJECT_ID /
    # FCM_SERVICE_ACCOUNT_FILE. Until implemented this is the logging stub.
    pass


def get_backend(channel: str) -> BaseBackend:
    if channel == NotificationEvent.Channel.IN_APP:
        return InAppBackend()
    if channel == NotificationEvent.Channel.SMS:
        return AfricasTalkingSmsBackend() if settings.SMS_BACKEND == "africastalking" else LoggingSmsBackend()
    if channel == NotificationEvent.Channel.PUSH:
        return FcmPushBackend() if settings.PUSH_BACKEND == "fcm" else LoggingPushBackend()
    raise ValueError(f"unknown channel {channel}")

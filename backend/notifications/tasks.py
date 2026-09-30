from celery import shared_task

from .backends import get_backend
from .models import NotificationEvent


@shared_task
def dispatch_notification(event_id: int):
    event = NotificationEvent.objects.select_related("user").filter(pk=event_id).first()
    if event is None or event.status != NotificationEvent.Status.PENDING:
        return
    get_backend(event.channel).send(event)


@shared_task
def retry_pending_notifications():
    """Beat safety net: dispatches SMS/push events left pending (e.g. the
    broker was down when they were created)."""
    for event_id in NotificationEvent.objects.filter(
        status=NotificationEvent.Status.PENDING
    ).exclude(channel=NotificationEvent.Channel.IN_APP).values_list("pk", flat=True)[:500]:
        dispatch_notification(event_id)

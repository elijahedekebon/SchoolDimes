import logging
from decimal import Decimal

from django.db import transaction
from django.utils import translation

from .backends import InAppBackend
from .labels import LABELLED_KEYS, LABELS
from .models import NotificationEvent, NotificationPreference
from .templates import TEMPLATES

logger = logging.getLogger("schooldimes.notifications")


class _SafeDict(dict):
    def __missing__(self, key):
        return ""


def fmt_amount(value) -> str:
    """UGX has no minor unit in practice: 20000 -> '20,000'; 1500.50 -> '1,500.50'."""
    amount = Decimal(str(value))
    if amount == amount.to_integral_value():
        return f"{amount:,.0f}"
    return f"{amount:,.2f}"


def _label(value):
    if isinstance(value, (list, tuple)):
        return ", ".join(str(LABELS.get(v, v)) for v in value)
    return str(LABELS.get(value, value))


def render(event_type: str, payload: dict, language: str) -> tuple[str, str]:
    """Renders (title, body) for an event in `language`."""
    title_tpl, body_tpl = TEMPLATES[event_type]
    with translation.override(language or "en"):
        context = _SafeDict(payload)
        for key in LABELLED_KEYS:
            if key in payload:
                context[f"{key}_label"] = _label(payload[key])
        return str(title_tpl) % context, str(body_tpl) % context


def get_preferences(user) -> NotificationPreference:
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    return pref


def _enqueue(event_id: int):
    from .tasks import dispatch_notification

    try:
        dispatch_notification.delay(event_id)
    except Exception:  # broker down: leave pending for retry_pending_notifications
        logger.exception("could not enqueue notification %s; left pending", event_id)


def notify(user, event_type: str, payload: dict | None = None) -> list[NotificationEvent]:
    """
    Creates one NotificationEvent per enabled channel for `user`, rendered in
    their preferred_language. In-app is delivered immediately (the row is the
    notification); SMS/push are dispatched by Celery after the surrounding
    transaction commits, so a rolled-back money movement never notifies.
    """
    if user is None or not user.is_active:
        return []
    if event_type not in TEMPLATES:
        raise ValueError(f"unknown notification event_type {event_type}")
    payload = payload or {}
    pref = get_preferences(user)
    title, body = render(event_type, payload, user.preferred_language)

    channels = []
    if pref.in_app_enabled:
        channels.append(NotificationEvent.Channel.IN_APP)
    if pref.sms_enabled:
        channels.append(NotificationEvent.Channel.SMS)
    if pref.push_enabled and user.push_tokens.exists():
        channels.append(NotificationEvent.Channel.PUSH)

    events = []
    for channel in channels:
        event = NotificationEvent.objects.create(
            user=user, event_type=event_type, payload=payload,
            channel=channel, title=title, body=body,
        )
        if channel == NotificationEvent.Channel.IN_APP:
            InAppBackend().send(event)
        else:
            transaction.on_commit(lambda eid=event.pk: _enqueue(eid))
        events.append(event)
    return events


def notify_guardians(student, event_type: str, payload: dict, *, exclude_user_ids=()):
    from accounts.models import User

    guardians = User.objects.filter(
        guardian_links__student=student, is_active=True
    ).exclude(pk__in=list(exclude_user_ids)).distinct()
    events = []
    for guardian in guardians:
        events += notify(guardian, event_type, payload)
    return events


def notify_school_admins(school_id, event_type: str, payload: dict):
    from accounts.models import User

    events = []
    for admin in User.objects.filter(
        school_id=school_id, role=User.Role.SCHOOL_ADMIN, is_active=True
    ):
        events += notify(admin, event_type, payload)
    return events

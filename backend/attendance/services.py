from datetime import date, datetime, time, timedelta

from django.db import IntegrityError, transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from cards.models import Card
from notifications.services import notify_guardians
from policies.services import KAMPALA
from pos.models import Device
from tenants.services import get_school_settings

from .models import AttendanceRecord

MAX_TAPS = 500


def device_may_record_attendance(device) -> bool:
    if device.device_role == Device.Role.ATTENDANCE:
        return True
    return device.device_role == Device.Role.CANTEEN and get_school_settings(device.school_id).attendance_on_canteen_devices


def kampala_day_range(day: date):
    start = datetime.combine(day, time.min, KAMPALA)
    return start, start + timedelta(days=1)


def _result(record, status):
    return {"idempotency_key": record.idempotency_key, "status": status, "record_id": record.pk,
            "student_id": record.student_id, "direction": record.direction, "reason": None}


def record_tap(device, raw: dict) -> dict:
    """Idempotent per (device, idempotency_key). Only cards of the device's
    own school are accepted (attendance is never cross-school)."""
    key = str(raw.get("idempotency_key") or "")[:128]
    if not key:
        return {"idempotency_key": None, "status": "rejected", "reason": "idempotency_key_required"}
    existing = AttendanceRecord.objects.filter(device=device, idempotency_key=key).first()
    if existing:
        return _result(existing, "duplicate")
    direction = raw.get("direction", AttendanceRecord.Direction.IN)
    if direction not in AttendanceRecord.Direction.values:
        return {"idempotency_key": key, "status": "rejected", "reason": "direction_invalid"}
    ts = parse_datetime(str(raw.get("device_local_timestamp") or ""))
    if ts is None:
        return {"idempotency_key": key, "status": "rejected", "reason": "timestamp_required"}
    if timezone.is_naive(ts):
        ts = timezone.make_aware(ts, KAMPALA)
    card = Card.objects.select_related("student").filter(card_uid=str(raw.get("card_uid", "")), school_id=device.school_id).first()
    if card is None:
        return {"idempotency_key": key, "status": "rejected", "reason": "unknown_card"}

    start, end = kampala_day_range(ts.astimezone(KAMPALA).date())
    first_in_today = direction == "in" and not AttendanceRecord.objects.filter(
        student=card.student, direction="in", device_local_timestamp__gte=start, device_local_timestamp__lt=end
    ).exists()
    try:
        with transaction.atomic():
            record = AttendanceRecord.objects.create(
                school_id=device.school_id, student=card.student, card=card, device=device,
                direction=direction, device_local_timestamp=ts, idempotency_key=key,
            )
    except IntegrityError:
        return _result(AttendanceRecord.objects.get(device=device, idempotency_key=key), "duplicate")
    if first_in_today and get_school_settings(device.school_id).attendance_notify_guardians:
        notify_guardians(card.student, "attendance_tap_in", {
            "student_id": card.student_id, "student_name": card.student.name,
            "time": ts.astimezone(KAMPALA).strftime("%H:%M"), "attendance_record_id": record.pk,
        })
    return _result(record, "created")


def record_taps(device, taps: list) -> list:
    results = []
    for raw in taps[:MAX_TAPS]:
        results.append(record_tap(device, raw) if isinstance(raw, dict)
                       else {"idempotency_key": None, "status": "rejected", "reason": "malformed"})
    Device.objects.filter(pk=device.pk).update(last_sync_at=timezone.now())
    return results



def build_roster(device, since=None) -> dict:
    """Part 3: the attendance device's offline roster -- every card of the
    device's school (lost cards included so they can be refused), with only
    what the gate shows. Incremental with ?since= like /pos/cache/."""
    from django.db.models import Q
    from django.utils import timezone

    from cards.models import Card

    now = timezone.now()
    cards = Card.objects.filter(school_id=device.school_id).select_related("student")
    if since is not None:
        cards = cards.filter(Q(updated_at__gt=since) | Q(student__updated_at__gt=since))
    return {
        "generated_at": now.isoformat(),
        "since": since.isoformat() if since else None,
        "full": since is None,
        "cards": [
            {"card_uid": c.card_uid, "status": c.status, "student_id": c.student_id,
             "student_display_name": c.student.name, "class_name": c.student.class_name,
             "photo_url": c.student.photo.url if c.student.photo else None}
            for c in cards
        ],
    }

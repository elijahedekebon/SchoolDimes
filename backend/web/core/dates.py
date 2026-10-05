"""Dates in Africa/Kampala -- the twin of lib/dates.ts."""
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from django.utils import timezone
from django.utils.dateparse import parse_date, parse_datetime

KAMPALA = ZoneInfo("Africa/Kampala")
_MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sept", "Oct", "Nov", "Dec"]


def kampala_today() -> str:
    return timezone.now().astimezone(KAMPALA).date().isoformat()


def shift_day(day: str, delta: int) -> str:
    return (date.fromisoformat(day) + timedelta(days=delta)).isoformat()


def valid_day(value, default):
    """A YYYY-MM-DD query value, or `default` when missing/invalid."""
    return value if value and parse_date(value) else default


def _as_datetime(value):
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, date):
        return None
    return parse_datetime(str(value))


def format_datetime(value) -> str:
    """en-GB medium date + short time in Kampala: '5 Oct 2026, 14:30'."""
    d = _as_datetime(value)
    if d is None:
        return "—" if not value else str(value)
    if timezone.is_naive(d):
        d = timezone.make_aware(d, KAMPALA)
    d = d.astimezone(KAMPALA)
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}, {d:%H:%M}"


def format_date(value) -> str:
    """'2026-10-05' stays as is (a calendar day); datetimes -> '5 Oct 2026'."""
    if value is None or value == "":
        return "—"
    if isinstance(value, date) and not isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, str) and parse_date(value) and len(value) == 10:
        return value
    d = _as_datetime(value)
    if d is None:
        return str(value)
    d = d.astimezone(KAMPALA)
    return f"{d.day} {_MONTHS[d.month - 1]} {d.year}"


def time_only(value) -> str:
    d = _as_datetime(value)
    return d.astimezone(KAMPALA).strftime("%H:%M") if d else "—"


def hours_since(value):
    d = _as_datetime(value)
    if d is None:
        return None
    return (timezone.now() - d).total_seconds() / 3600

"""Money display helpers -- the Python twin of the dashboard's lib/money.ts.

Amounts are decimal strings / Decimals ("5000.00"). Never floats: parsing
goes to integer cents, formatting is string-based."""
import re
from decimal import Decimal

_RE = re.compile(r"^(-)?(\d+)(?:\.(\d{1,2}))?$")


def to_cents(value):
    """'15000.5' -> 1500050; None/''/garbage -> None."""
    if value is None or value == "":
        return None
    s = format(value, "f") if isinstance(value, Decimal) else str(value).strip()
    m = _RE.match(s)
    if not m:
        return None
    cents = int(m.group(2)) * 100 + int((m.group(3) or "").ljust(2, "0") or "0")
    return -cents if m.group(1) else cents


def from_cents(cents: int) -> str:
    neg = cents < 0
    a = -cents if neg else cents
    return f"{'-' if neg else ''}{a // 100}.{a % 100:02d}"


def format_ugx(value, prefix=True) -> str:
    """'15000.50' -> 'UGX 15,000.50'; '15000.00' -> 'UGX 15,000'; None -> '—'."""
    c = to_cents(value)
    if c is None:
        return "—"
    neg = c < 0
    a = -c if neg else c
    whole = f"{a // 100:,}"
    frac = a % 100
    body = whole if frac == 0 else f"{whole}.{frac:02d}"
    return f"{'-' if neg else ''}{'UGX ' if prefix else ''}{body}"


def compare_money(a, b) -> int:
    x, y = to_cents(a) or 0, to_cents(b) or 0
    return (x > y) - (x < y)


def is_valid_amount(value) -> bool:
    """Positive, at most 2 decimal places."""
    c = to_cents(value)
    return c is not None and c > 0


def shillings(value) -> int:
    """Whole shillings, for chart geometry only (never for money maths)."""
    return (to_cents(value) or 0) // 100

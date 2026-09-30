from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.utils.translation import gettext as _

from .exceptions import ServiceError

CENT = Decimal("0.01")


def validate_amount(value) -> Decimal:
    """Cross-cutting rule 5: request amounts are always positive; direction
    comes from the operation. Rejects zero, negative, non-numeric, more than
    2 decimal places, and anything above settings.MAX_TRANSACTION_AMOUNT."""
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ServiceError("amount_invalid", _("Amount must be a number."))
    if not amount.is_finite() or amount <= 0:
        raise ServiceError("amount_invalid", _("Amount must be greater than zero."))
    if amount != amount.quantize(CENT):
        raise ServiceError("amount_invalid", _("Amount may have at most 2 decimal places."))
    if amount > Decimal(str(settings.MAX_TRANSACTION_AMOUNT)):
        raise ServiceError(
            "amount_too_large",
            _("Amount exceeds the maximum allowed per transaction (%(max)s).")
            % {"max": settings.MAX_TRANSACTION_AMOUNT},
        )
    return amount.quantize(CENT)

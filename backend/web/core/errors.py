"""Turns service/validation exceptions into what ErrorAlert showed: the
backend's own (translated) message plus its reason code(s)."""
from dataclasses import dataclass, field

from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.translation import gettext as _
from rest_framework.exceptions import APIException, ValidationError

from core.exceptions import InsufficientFundsError, ServiceError


@dataclass
class WebError:
    display: str
    code: str | None = None
    violations: list = field(default_factory=list)
    status: int = 400

    @property
    def codes(self):
        if not self.code:
            return ""
        return ", ".join([self.code] + [v for v in self.violations if v != self.code])


def _flatten(detail):
    if isinstance(detail, dict):
        parts = []
        for k, v in detail.items():
            text = " ".join(_flatten(v)) if isinstance(v, (list, dict)) else str(v)
            parts.append(text if k == "non_field_errors" else f"{k}: {text}")
        return parts
    if isinstance(detail, list):
        out = []
        for v in detail:
            out += _flatten(v) if isinstance(v, (list, dict)) else [str(v)]
        return out
    return [str(detail)]


def as_error(exc) -> WebError:
    if isinstance(exc, ServiceError):
        return WebError(exc.message, exc.code, list(exc.extra.get("violations", [])), exc.status)
    if isinstance(exc, InsufficientFundsError):
        return WebError(_("Insufficient funds."), "insufficient_funds", status=422)
    if isinstance(exc, ValidationError):
        return WebError(" · ".join(_flatten(exc.detail)), None, status=400)
    if isinstance(exc, APIException):
        detail = exc.detail
        code = detail.code if hasattr(detail, "code") else None
        return WebError(" · ".join(_flatten(detail)), code, status=exc.status_code)
    if isinstance(exc, DjangoValidationError):
        return WebError(" · ".join(exc.messages), None)
    if isinstance(exc, WebError):
        return exc
    raise exc


HANDLED = (ServiceError, InsufficientFundsError, APIException, DjangoValidationError)

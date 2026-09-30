from django.utils.translation import gettext as _
from rest_framework.response import Response
from rest_framework.views import exception_handler

from .exceptions import InsufficientFundsError, ServiceError


def api_exception_handler(exc, context):
    """DRF's default handler, plus a uniform `{code, detail}` body for
    business-rule refusals raised from service functions."""
    if isinstance(exc, ServiceError):
        body = {"code": exc.code, "detail": exc.message}
        body.update(exc.extra)
        return Response(body, status=exc.status)
    if isinstance(exc, InsufficientFundsError):
        return Response(
            {"code": "insufficient_funds", "detail": _("Insufficient funds.")}, status=422
        )
    return exception_handler(exc, context)

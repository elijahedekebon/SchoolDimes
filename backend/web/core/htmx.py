"""HTMX response helpers."""
import json

from django.http import HttpResponse


def is_htmx(request) -> bool:
    return request.headers.get("HX-Request") == "true"


def hx_target(request):
    return request.headers.get("HX-Target") if is_htmx(request) else None


def hx_redirect(url):
    response = HttpResponse(status=200)
    response["HX-Redirect"] = url
    return response


def hx_done(message=None, *, close=True, refresh=True, events=None):
    """What ConfirmAction did on success: close the dialog, show a toast,
    reload the list(s) on the page."""
    triggers = dict(events or {})
    if close:
        triggers["sd-close"] = True
    if message:
        triggers["sd-toast"] = {"message": str(message)}
    if refresh:
        triggers["sd-refresh"] = True
    response = HttpResponse("")
    response["HX-Reswap"] = "none"
    response["HX-Trigger"] = json.dumps(triggers)
    return response

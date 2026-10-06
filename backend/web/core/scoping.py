"""The one tenant-scoping helper every web view uses.

Each name maps to the SAME queryset function the API viewset's
`get_queryset()` calls, so the web sees exactly what the API would show the
signed-in user -- scoped from `request.user`, never from a school id in the
URL or form. Filters are the API's query parameters (same names)."""
from django.http import Http404
from django.utils.module_loading import import_string

SCOPES = {
    "notifications": "notifications.services.inbox",
    # Section B
    "devices": "pos.services.devices_for",
    "transactions": "pos.services.transactions_for",
    "shortfalls": "pos.services.shortfalls_for",
    "review_items": "web.core.scoping.review_items",
    "disputes": "disputes.services.disputes_for",
    "p2p_alerts": "wallets.p2p.alerts_for",
    "data_requests": "privacy.services.data_requests_for",
    # Section C/D
    "students": "students.access.students_for",
    "student": "web.core.scoping.student_detail",
    "guardians": "students.services.guardians_for",
    "verifications": "accounts.services.verifications_for",
    "cards": "cards.services.cards_for",
    "wallets": "wallets.services.wallets_for",
    "goals": "wallets.services.goals_for",
    "policies": "policies.services.policies_for",
    "categories": "policies.services.categories_for",
    "products": "policies.services.products_for",
    "merchants": "merchants.services.merchants_for",
    "attendance": "attendance.services.attendance_for",
    "staff": "accounts.services.staff_for",
}


def student_detail(user, params):
    """A single student as GET /students/{id}/ sees it (no list filters)."""
    from students.access import students_for

    return students_for(user, params, for_list=False)


def review_items(user, params):
    """A single review-queue row (what the API's ShortfallViewSet detail/resolve sees)."""
    from pos.services import shortfalls_for

    return shortfalls_for(user, params, for_list=False)


def scoped(user, name, params=None):
    return import_string(SCOPES[name])(user, params or {})


def scoped_object(user, name, pk, params=None):
    """An object visible to `user`, or 404 (another school's object included)."""
    try:
        pk = int(pk)
    except (TypeError, ValueError):
        raise Http404
    qs = scoped(user, name, params)
    obj = qs.filter(pk=pk).first() if hasattr(qs, "filter") else next((o for o in qs if o.pk == pk), None)
    if obj is None:
        raise Http404
    return obj

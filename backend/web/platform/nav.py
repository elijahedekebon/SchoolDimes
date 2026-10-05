"""The back-office sidebar (was src/app/platform/layout.tsx NAV)."""
from django.utils.translation import gettext_lazy as _

NAV = [
    {"href": "/platform", "label": _("Schools"), "exact": True},
    {"href": "/platform/onboard", "label": _("Onboard a school")},
    {"href": "/platform/referrals", "label": _("Referrals")},
    {"href": "/platform/support", "label": _("Support")},
    {"href": "/platform/payment-issues", "label": _("Payment issues")},
    {"href": "/platform/audit-log", "label": _("Audit log")},
    {"href": "/platform/tips", "label": _("Financial tips")},
]

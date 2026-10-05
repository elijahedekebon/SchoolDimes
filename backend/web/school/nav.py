"""The school admin sidebar (was src/app/school/layout.tsx NAV): same items, same order."""
from django.utils.translation import gettext_lazy as _

NAV = [
    {"href": "/school", "label": _("Overview"), "exact": True},
    {"href": "/school/sales", "label": _("Sales")},
    {"href": "/school/reconciliation", "label": _("Reconciliation")},
    {"href": "/school/shortfalls", "label": _("Review queue")},
    {"href": "/school/analytics", "label": _("Analytics")},
    {"href": "/school/students", "label": _("Students")},
    {"href": "/school/guardians", "label": _("Guardians & KYC")},
    {"href": "/school/cards", "label": _("Cards")},
    {"href": "/school/devices", "label": _("Devices")},
    {"href": "/school/merchants", "label": _("Merchants")},
    {"href": "/school/products", "label": _("Products")},
    {"href": "/school/policy", "label": _("Policy & settings")},
    {"href": "/school/staff", "label": _("Staff accounts")},
    {"href": "/school/fees", "label": _("Fees")},
    {"href": "/school/attendance", "label": _("Attendance")},
    {"href": "/school/pooled-funds", "label": _("Pooled funds")},
    {"href": "/school/disputes", "label": _("Disputes")},
    {"href": "/school/p2p-alerts", "label": _("P2P alerts")},
    {"href": "/school/privacy", "label": _("Data requests")},
    {"href": "/school/tips", "label": _("Financial tips")},
    {"href": "/school/payment-issues", "label": _("Payment issues")},
]

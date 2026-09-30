"""Translated labels for machine codes that appear inside notification
payloads (reasons, statuses, rule names). services.render() adds a
`<key>_label` entry for each of these payload keys."""
from django.utils.translation import gettext_lazy as _

LABELS = {
    # failure reasons
    "expired": _("the payment request expired"),
    "declined": _("the payment was declined"),
    "aggregator_error": _("the payment provider returned an error"),
    "insufficient_funds": _("insufficient funds"),
    "payout_failed": _("the mobile money transfer failed"),
    "card_frozen": _("card frozen"),
    "card_lost": _("card reported lost"),
    "daily_cap_exceeded": _("daily spending limit exceeded"),
    "weekly_cap_exceeded": _("weekly spending limit exceeded"),
    "per_transaction_cap_exceeded": _("single purchase limit exceeded"),
    "category_blocked": _("blocked category"),
    "category_not_allowed": _("category not allowed"),
    "item_blocked": _("blocked item"),
    "merchant_blocked": _("blocked merchant"),
    "exceeds_offline_ceiling": _("exceeded the offline spending limit"),
    "shortfall": _("not enough balance"),
    # statuses
    "open": _("open"),
    "under_review": _("under review"),
    "resolved_refunded": _("resolved — refunded"),
    "resolved_denied": _("resolved — not refunded"),
    "pending": _("pending"),
    "in_progress": _("in progress"),
    "completed": _("completed"),
    "rejected": _("rejected"),
    # p2p alert rules
    "many_distinct_senders": _("received money from many different students"),
    "repeated_near_cap": _("repeatedly sent amounts close to the daily limit"),
    # data request types
    "export": _("data export"),
    "correction": _("correction"),
    "deletion": _("deletion"),
}

LABELLED_KEYS = ("reason", "status", "rule", "request_type", "flags")

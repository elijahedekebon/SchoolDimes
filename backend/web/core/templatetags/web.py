"""Template tags/filters replacing the dashboard's ui.tsx and lib helpers."""
import json

from django import template
from django.utils.html import format_html, format_html_join
from django.utils.safestring import mark_safe
from django.utils.translation import gettext as _

from ..dates import format_date, format_datetime, time_only
from ..money import format_ugx, shillings

register = template.Library()

STATUS_COLORS = {
    "active": "green", "approved": "green", "applied": "green", "confirmed": "green", "verified": "green",
    "completed": "green", "resolved": "green", "resolved_refunded": "green", "redeemed": "green",
    "succeeded": "green",
    "open": "blue",
    "pending": "yellow", "pending_payment": "yellow", "in_progress": "yellow", "under_review": "yellow",
    "recovery_pending": "yellow",
    "frozen": "cyan",
    "shortfall": "orange",
    "duplicate": "gray", "closed": "gray", "dismissed": "gray", "reviewed": "gray", "disbursed": "gray",
    "revoked": "red", "lost": "red", "failed": "red", "rejected": "red", "expired": "red", "suspended": "red",
    "cancelled": "red", "resolved_denied": "red",
}


@register.filter
def ugx(value):
    """formatUGX: 'UGX 15,000' / 'UGX 15,000.50' / '—'."""
    return format_ugx(value)


@register.filter
def money(value, color=""):
    """The <Money> component: tabular figures, no wrapping, optional colour."""
    cls = f"money c-{color}" if color else "money"
    return format_html('<span class="{}">{}</span>', cls, format_ugx(value))


@register.filter
def signed(entry_amount, direction):
    """Ledger rows: debits shown negative."""
    return f"-{entry_amount}" if direction == "debit" else entry_amount


@register.filter
def dt(value):
    return format_datetime(value)


@register.filter
def d(value):
    return format_date(value)


@register.filter(name="time_only")
def time_only_filter(value):
    return time_only(value)


@register.filter
def human(value):
    """'resolved_refunded' -> 'resolved refunded'."""
    return "" if value is None else str(value).replace("_", " ")


@register.filter
def get(mapping, key):
    if mapping is None:
        return None
    try:
        return mapping.get(key) if hasattr(mapping, "get") else mapping[key]
    except (KeyError, IndexError, TypeError):
        return None


@register.filter
def whole_shillings(value):
    return shillings(value)


@register.filter
def to_json(value):
    return mark_safe(json.dumps(value, default=str))


@register.filter
def dash(value):
    return "—" if value in (None, "", []) else value


@register.simple_tag
def status_badge(status):
    if not status:
        return mark_safe('<span class="dimmed">—</span>')
    return format_html('<span class="badge badge-light c-{}">{}</span>', STATUS_COLORS.get(status, "gray"),
                       str(status).replace("_", " "))


@register.simple_tag
def badge(text, color="gray", variant="light", size=""):
    return format_html('<span class="badge badge-{} c-{} {}">{}</span>', variant, color,
                       f"badge-{size}" if size else "", text)


@register.simple_tag
def flags(values):
    if not values:
        return ""
    return format_html('<span class="group gap-4">{}</span>', format_html_join(
        "", '<span class="badge badge-outline badge-xs c-orange">{}</span>',
        ((str(f).replace("_", " "),) for f in values)))


@register.inclusion_tag("core/components/error_alert.html")
def error_alert(error, title=None):
    return {"error": error, "title": title or _("Something went wrong")}


@register.inclusion_tag("core/components/stat.html")
def stat(label, value, hint=None, href=None, color=None):
    return {"label": label, "value": value, "hint": hint, "href": href, "color": color}


@register.inclusion_tag("core/components/pagination.html", takes_context=True)
def pagination(context, page, target, include=None):
    """Mantine <Pagination>: only when there is more than one page."""
    return {"page": page, "target": target, "include": include, "path": context["request"].path}


@register.inclusion_tag("core/components/empty_row.html")
def empty_row(colspan, message=None):
    return {"colspan": colspan, "message": message or _("Nothing here yet.")}


@register.inclusion_tag("core/components/choice_filter.html")
def choice_filter(name, label, value, options):
    """ChoiceFilter: a select with an 'All' first option; options are (value, label) pairs."""
    return {"name": name, "label": label, "value": value or "", "options": options}


@register.inclusion_tag("core/components/language_switcher.html", takes_context=True)
def language_switcher(context):
    from django.utils.translation import get_language

    from ..views import LANGUAGES

    request = context["request"]
    return {"languages": LANGUAGES, "current": (get_language() or "en")[:2], "next": request.get_full_path(),
            "csrf_token": context.get("csrf_token")}


class PageHeaderNode(template.Node):
    def __init__(self, title, subtitle, nodelist):
        self.title, self.subtitle, self.nodelist = title, subtitle, nodelist

    def render(self, context):
        title = self.title.resolve(context)
        subtitle = self.subtitle.resolve(context) if self.subtitle else ""
        actions = self.nodelist.render(context).strip()
        return template.loader.render_to_string(
            "core/components/page_header.html", {"title": title, "subtitle": subtitle, "actions": mark_safe(actions)})


@register.tag
def pageheader(parser, token):
    """{% pageheader title [subtitle] %}actions…{% endpageheader %} (PageHeader)."""
    bits = token.split_contents()
    title = parser.compile_filter(bits[1])
    subtitle = parser.compile_filter(bits[2]) if len(bits) > 2 else None
    nodelist = parser.parse(("endpageheader",))
    parser.delete_first_token()
    return PageHeaderNode(title, subtitle, nodelist)

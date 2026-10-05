from django.core.paginator import Paginator

PAGE_SIZE = 20  # the dashboard's usePaginated default


def paginate(qs, params, page_size=PAGE_SIZE):
    """Server-side paging like the API's (?page=, 20 per page)."""
    if hasattr(qs, "ordered") and not qs.ordered:
        qs = qs.order_by("-pk")
    paginator = Paginator(qs, page_size)
    return paginator.get_page(params.get("page") or 1)

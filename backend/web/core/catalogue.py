"""id -> name maps for categories, products and merchants (was lib/catalogue.ts)."""
from . import scoping


def catalogue(user):
    return {
        "categories": dict(scoping.scoped(user, "categories").values_list("id", "name")[:100]),
        "products": dict(scoping.scoped(user, "products").values_list("id", "name")[:100]),
        "merchants": dict(scoping.scoped(user, "merchants").values_list("id", "name")[:100]),
    }


def names(ids, mapping):
    return ", ".join(mapping.get(i, f"#{i}") for i in ids) if ids else "—"

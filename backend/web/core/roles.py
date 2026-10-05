"""Role-based routing -- the twin of lib/roles.ts (same rules).

- school_admin   -> /school/...
- platform_admin -> /platform/...
- student        -> /student (read-only portal)
- parent, canteen_staff, merchant_staff -> refused (mobile parent app / POS app)
"""
from dataclasses import dataclass
from urllib.parse import quote

PUBLIC_PREFIXES = ("/login", "/logout", "/locale", "/give", "/static", "/api", "/admin", "/media", "/favicon")
HOMES = {"school_admin": "/school", "platform_admin": "/platform", "student": "/student"}


def home_for(role):
    return HOMES.get(role)


def is_public_path(path: str) -> bool:
    if path == "/":
        return False
    return any(path == p or path.startswith(p + "/") for p in PUBLIC_PREFIXES)


def _area(path: str) -> str:
    if path == "/":
        return "root"
    seg = path.split("/")[1]
    return seg if seg in ("school", "platform", "student") else "other"


@dataclass
class RouteDecision:
    kind: str  # allow | redirect | refuse
    to: str = ""


def decide_route(role, path: str) -> RouteDecision:
    if is_public_path(path):
        return RouteDecision("allow")
    if not role:
        return RouteDecision("redirect", f"/login?next={quote(path, safe='/')}")
    home = home_for(role)
    if not home:
        return RouteDecision("refuse")
    area = _area(path)
    if area == "root":
        return RouteDecision("redirect", home)
    if area in ("school", "platform", "student"):
        return RouteDecision("allow") if home == f"/{area}" else RouteDecision("redirect", home)
    return RouteDecision("allow")

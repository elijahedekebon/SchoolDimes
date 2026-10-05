from .branding import palette_for


def app_frame(request):
    """The AppFrame's school name, logo and brand palette, and the area nav."""
    path = request.path
    area = path.split("/")[1] if path.count("/") >= 1 else ""
    if area not in ("school", "platform", "student"):
        return {}
    user = getattr(request, "user", None)
    if not user or not user.is_authenticated:
        return {}
    from importlib import import_module

    nav = []
    for item in import_module(f"web.{area}.nav").NAV:
        href = item["href"]
        active = path == href if item.get("exact") else path == href or path.startswith(href + "/")
        nav.append({**item, "active": active})
    school = user.school if user.school_id else None
    branding = (school.branding or {}) if school else {}
    return {
        "frame_area": area,
        "frame_nav": nav,
        "frame_school": school,
        "frame_logo": branding.get("logo_url"),
        "frame_palette": palette_for(branding),
    }

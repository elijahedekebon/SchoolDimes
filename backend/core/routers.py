from rest_framework.routers import DefaultRouter


class OptionalSlashRouter(DefaultRouter):
    """Part 2+ router: accepts `/path/` (Part 1's canonical form, used in the
    docs) and `/path` (the form written in the Part 2 spec). Part 1's own
    routers are left untouched."""

    include_format_suffixes = False

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.trailing_slash = "/?"

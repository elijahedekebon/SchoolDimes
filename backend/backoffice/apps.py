from django.apps import AppConfig


class BackofficeConfig(AppConfig):
    """Part 4A: platform back-office (platform_admin only). No models of its
    own: school onboarding, cross-school stats and review lists composed
    from the other apps' services."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "backoffice"

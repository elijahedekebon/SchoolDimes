from django.apps import AppConfig


class PooledFundsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "pooled_funds"

    def ready(self):
        from . import receivers  # noqa: F401

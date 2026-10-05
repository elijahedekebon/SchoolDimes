from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class AuthThrottle(SimpleRateThrottle):
    """Per-client-IP throttle for credential endpoints (login, register).
    Backed by the default cache (Redis). Rate: AUTH_THROTTLE_RATE ("10/min")."""

    scope = "auth"

    def get_rate(self):
        return settings.AUTH_THROTTLE_RATE

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}

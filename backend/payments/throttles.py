from django.conf import settings
from rest_framework.throttling import SimpleRateThrottle


class PublicTopUpThrottle(SimpleRateThrottle):
    """Per-client-IP throttle for the unauthenticated /public/ endpoints.
    Backed by the default cache (Redis). The rate is read from settings on
    every request (PUBLIC_TOPUP_THROTTLE_RATE, e.g. "20/min")."""

    scope = "public_topup"

    def get_rate(self):
        return settings.PUBLIC_TOPUP_THROTTLE_RATE

    def get_cache_key(self, request, view):
        return self.cache_format % {"scope": self.scope, "ident": self.get_ident(request)}

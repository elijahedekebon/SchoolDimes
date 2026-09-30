import hashlib
from datetime import timedelta

from django.utils import timezone
from rest_framework import authentication, exceptions, permissions

from .models import Device

HEARTBEAT_EVERY = timedelta(seconds=60)


def hash_token(raw: str) -> str:
    """Device tokens are 256-bit random strings, so a fast hash is enough
    (no salt/stretching needed, unlike human PINs/passwords)."""
    return hashlib.sha256(raw.encode()).hexdigest()


class DevicePrincipal:
    """Stands in for request.user on device-authenticated requests."""

    is_authenticated = True
    is_anonymous = False
    is_active = True
    role = "device"
    pk = None
    id = None

    def __init__(self, device):
        self.device = device
        self.school_id = device.school_id

    def __str__(self):
        return f"device:{self.device.pk}"


class DeviceTokenAuthentication(authentication.BaseAuthentication):
    """`Authorization: Device <raw token>`. Revoked devices are refused
    immediately (the token lookup only matches active devices). Every call
    is a heartbeat: last_seen_at is refreshed (at most once a minute)."""

    keyword = "Device"

    def authenticate(self, request):
        header = authentication.get_authorization_header(request).decode(errors="ignore").split()
        if not header or header[0] != self.keyword:
            return None
        if len(header) != 2:
            raise exceptions.AuthenticationFailed("Invalid device token header.")
        device = Device.objects.select_related("school").filter(token_hash=hash_token(header[1])).first()
        if device is None or device.status != Device.Status.ACTIVE:
            raise exceptions.AuthenticationFailed("Invalid or revoked device token.")
        now = timezone.now()
        if device.last_seen_at is None or now - device.last_seen_at > HEARTBEAT_EVERY:
            version = request.headers.get("X-App-Version", "")[:32]
            Device.objects.filter(pk=device.pk).update(last_seen_at=now, **({"app_version": version} if version else {}))
            device.last_seen_at = now
        return DevicePrincipal(device), device

    def authenticate_header(self, request):
        return self.keyword


class IsDevice(permissions.BasePermission):
    """Allows device principals, optionally restricted to certain roles
    (set `device_roles` on the view)."""

    def has_permission(self, request, view):
        principal = request.user
        if not isinstance(principal, DevicePrincipal):
            return False
        roles = getattr(view, "device_roles", None)
        return roles is None or principal.device.device_role in roles

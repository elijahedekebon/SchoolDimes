from .models import AuditLog
from .permissions import is_platform_admin


def audit(actor, action, target=None, *, school_id=None, details=None, force=False):
    """Records a privileged write. By default only platform_admin writes are
    logged (the cross-tenant role); pass force=True to log any actor."""
    if not (force or is_platform_admin(actor)):
        return None
    if school_id is None and target is not None:
        school_id = getattr(target, "school_id", None)
    return AuditLog.objects.create(
        actor=actor if getattr(actor, "pk", None) else None,
        actor_role=getattr(actor, "role", "") or "",
        school_id=school_id,
        action=action,
        target_type=type(target).__name__ if target is not None else "",
        target_id=str(getattr(target, "pk", "") or ""),
        details=details or {},
    )


class AuditPlatformAdminWritesMixin:
    """ViewSet mixin: audit-logs create/update/destroy done by platform_admin."""

    def perform_create(self, serializer):
        super().perform_create(serializer)
        audit(self.request.user, f"{self.basename}.create", serializer.instance)

    def perform_update(self, serializer):
        super().perform_update(serializer)
        audit(self.request.user, f"{self.basename}.update", serializer.instance)

    def perform_destroy(self, instance):
        audit(self.request.user, f"{self.basename}.destroy", instance)
        super().perform_destroy(instance)

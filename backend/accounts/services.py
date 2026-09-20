from django.utils import timezone


def mark_guardian_verification(verification, *, status, verified_at=None):
    """Transition a GuardianVerification to a new status. Single choke point
    so later parts (e.g. an admin review workflow) don't hand-edit the model."""
    verification.status = status
    if status == verification.Status.VERIFIED:
        verification.verified_at = verified_at or timezone.now()
    verification.save(update_fields=["status", "verified_at", "updated_at"])
    return verification

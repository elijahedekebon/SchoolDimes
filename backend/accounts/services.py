from django.utils import timezone


def mark_guardian_verification(verification, *, status, verified_at=None):
    """Transition a GuardianVerification to a new status. Single choke point
    so later parts (e.g. an admin review workflow) don't hand-edit the model."""
    verification.status = status
    if status == verification.Status.VERIFIED:
        verification.verified_at = verified_at or timezone.now()
    verification.save(update_fields=["status", "verified_at", "updated_at"])
    return verification


def review_guardian_verification(verification, *, reviewer, status, notes=""):
    """Part 4A: school/platform admin approves (verified) or rejects a KYC-lite
    submission, with notes. Goes through mark_guardian_verification()."""
    from core.audit import audit

    mark_guardian_verification(verification, status=status)
    if status != verification.Status.VERIFIED:
        verification.verified_at = None
    verification.review_notes = notes or ""
    verification.reviewed_by = reviewer
    verification.reviewed_at = timezone.now()
    verification.save(update_fields=["verified_at", "review_notes", "reviewed_by", "reviewed_at", "updated_at"])
    audit(reviewer, "guardian_verification.review", verification, details={"status": status})
    return verification

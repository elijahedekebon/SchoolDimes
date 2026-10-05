"""
Privacy: data export and deletion-by-redaction.

The ledger is the audit trail and is NEVER deleted. A deletion request is
fulfilled by redacting personal data and deactivating access while keeping
every financial record (ledger entries, deposits, POS sales, fee payments)
-- see RETENTION_NOTICE, which is returned to the requester verbatim.
"""
from django.db import transaction
from django.utils import timezone
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy

from accounts.models import GuardianVerification
from cards.models import Card
from core.audit import audit
from core.exceptions import ServiceError
from notifications.services import notify
from students.models import Student
from wallets.models import LedgerEntry, Wallet

from .models import DataRequest

RETENTION_NOTICE = gettext_lazy(
    "Your personal details have been removed and access deactivated. Financial records "
    "(the ledger of payments, top-ups and purchases) are kept, without your personal details, "
    "because the law and the school's audit require an unaltered payment history. They are "
    "linked only to a redacted placeholder."
)


def _money(value):
    return str(value)


def _ledger(wallet):
    return [
        {"id": e.pk, "created_at": e.created_at.isoformat(), "direction": e.direction, "amount": _money(e.amount),
         "entry_type": e.entry_type, "reference_id": e.reference_id, "description": e.description}
        for e in LedgerEntry.objects.filter(wallet=wallet).order_by("created_at", "id")
    ]


def my_data(user) -> dict:
    """Everything stored about a parent and their linked students. Never
    includes pin_hash, other families' students, or system wallets."""
    verification = GuardianVerification.objects.filter(parent=user).first()
    students = []
    for student in Student.objects.filter(guardian_links__parent=user).select_related("school").distinct():
        students.append({
            "id": student.pk,
            "name": student.name,
            "class_name": student.class_name,
            "date_of_birth": student.date_of_birth.isoformat() if student.date_of_birth else None,
            "photo_url": student.photo.url if student.photo else None,
            "school": {"id": student.school_id, "name": student.school.name},
            "relationship": student.guardian_links.get(parent=user).relationship,
            "cards": [
                {"card_uid": c.card_uid, "status": c.status, "biometric_enrolled": c.biometric_enrolled,
                 "issued_at": c.issued_at.isoformat()}
                for c in Card.objects.filter(student=student)
            ],
            "wallets": [
                {"id": w.pk, "wallet_type": w.wallet_type, "balance": _money(w.cached_balance), "ledger": _ledger(w)}
                for w in Wallet.objects.filter(student=student).order_by("wallet_type")
            ],
        })
    return {
        "generated_at": timezone.now().isoformat(),
        "profile": {
            "id": user.pk, "email": user.email, "full_name": user.full_name, "phone_number": user.phone_number,
            "role": user.role, "preferred_language": user.preferred_language,
            "date_joined": user.date_joined.isoformat(),
        },
        "guardian_verification": None if verification is None else {
            "status": verification.status, "full_name": verification.full_name,
            "id_document_type": verification.id_document_type, "id_number": verification.id_number,
            "verified_at": verification.verified_at.isoformat() if verification.verified_at else None,
        },
        "students": students,
    }


def my_data_csv_rows(data: dict):
    yield ["section", "student", "field_or_date", "value_or_direction", "amount", "entry_type", "reference_id", "description"]
    for k, v in data["profile"].items():
        yield ["profile", "", k, v, "", "", "", ""]
    if data["guardian_verification"]:
        for k, v in data["guardian_verification"].items():
            yield ["guardian_verification", "", k, v, "", "", "", ""]
    for s in data["students"]:
        for k in ("name", "class_name", "date_of_birth", "relationship"):
            yield ["student", s["name"], k, s[k], "", "", "", ""]
        yield ["student", s["name"], "school", s["school"]["name"], "", "", "", ""]
        for c in s["cards"]:
            yield ["card", s["name"], c["card_uid"], c["status"], "", "", "", ""]
        for w in s["wallets"]:
            yield ["wallet", s["name"], w["wallet_type"], "balance", w["balance"], "", "", ""]
            for e in w["ledger"]:
                yield [f"ledger:{w['wallet_type']}", s["name"], e["created_at"], e["direction"], e["amount"],
                       e["entry_type"], e["reference_id"], e["description"]]


def create_request(user, *, request_type, subject, student=None, details=""):
    if request_type not in DataRequest.RequestType.values or subject not in DataRequest.Subject.values:
        raise ServiceError("request_invalid", _("Unknown request type or subject."))
    if subject == DataRequest.Subject.STUDENT:
        if student is None or not student.guardian_links.filter(parent=user).exists():
            raise ServiceError("not_found", _("Student not found."), status=404)
        school_id = student.school_id
    else:
        student = None
        first = Student.objects.filter(guardian_links__parent=user).order_by("pk").first()
        school_id = first.school_id if first else user.school_id
    return DataRequest.objects.create(requested_by=user, request_type=request_type, subject=subject,
                                      student=student, school_id=school_id, details=details[:5000])


def _redact_student(student):
    for wallet in Wallet.objects.filter(student=student):
        if wallet.cached_balance != 0:
            raise ServiceError("balance_not_zero", _(
                "The student's wallets still hold money. Withdraw savings or spend/refund the balance before deletion."
            ), status=409)
    student.name = f"Redacted student {student.pk}"
    student.class_name = ""
    student.date_of_birth = None
    if student.photo:
        student.photo.delete(save=False)
    student.photo = None
    student.save()
    Card.objects.filter(student=student).exclude(status=Card.Status.LOST).update(status=Card.Status.LOST, updated_at=timezone.now())
    student.recurring_topups.update(active=False)
    student.topup_links.update(active=False, revoked_at=timezone.now())


def _redact_user(user):
    user.email = f"redacted-{user.pk}@redacted.invalid"
    user.full_name = ""
    user.phone_number = ""
    user.is_active = False
    user.set_unusable_password()
    user.save()
    GuardianVerification.objects.filter(parent=user).update(full_name="Redacted", id_number="REDACTED")
    user.push_tokens.all().delete()
    user.notifications.all().delete()  # messages, not financial records
    user.recurring_topups.update(active=False)
    user.topup_links.update(active=False, revoked_at=timezone.now())


def handle_request(actor, request: DataRequest, *, status, notes=""):
    """school_admin of the request's school. Completing a DELETION request
    performs the redaction (irreversible) in the same transaction."""
    if status not in (DataRequest.Status.IN_PROGRESS, DataRequest.Status.COMPLETED, DataRequest.Status.REJECTED):
        raise ServiceError("status_invalid", _("status must be in_progress, completed or rejected."))
    if request.status in (DataRequest.Status.COMPLETED, DataRequest.Status.REJECTED):
        raise ServiceError("request_closed", _("This request is already closed."), status=409)
    requester = request.requested_by
    with transaction.atomic():
        if status == DataRequest.Status.COMPLETED and request.request_type == DataRequest.RequestType.DELETION:
            if request.subject == DataRequest.Subject.STUDENT:
                _redact_student(request.student)
            else:
                for student in Student.objects.filter(guardian_links__parent=requester):
                    if student.guardian_links.count() == 1:  # sole guardian: the child's data goes too
                        _redact_student(student)
            notes = f"{notes}\n\n{RETENTION_NOTICE}".strip()
        request.status, request.notes = status, notes
        request.handled_by, request.handled_at = actor, timezone.now()
        request.save()
        self_deletion = (status == DataRequest.Status.COMPLETED
                         and request.request_type == DataRequest.RequestType.DELETION
                         and request.subject == DataRequest.Subject.SELF)
        if self_deletion:
            _redact_user(requester)  # the account is gone; there is no one left to notify
        else:
            notify(requester, "data_request_updated", {
                "request_id": request.pk, "request_type": request.request_type, "status": status,
            })
    audit(actor, f"data_request.{status}", request, force=True)
    return request



def data_requests_for(user, params):
    """Parents: their own requests. school_admin: requests about the school's
    students or from their parents. platform_admin: all. ?status=, ?request_type=."""
    from django.db.models import Q

    from core.permissions import is_platform_admin, is_school_admin

    qs = DataRequest.objects.all()
    for f in ("status", "request_type"):
        if params.get(f):
            qs = qs.filter(**{f: params[f]})
    if is_platform_admin(user):
        return qs
    if is_school_admin(user):
        return qs.filter(Q(school_id=user.school_id)
                         | Q(requested_by__guardian_links__student__school_id=user.school_id)).distinct()
    return qs.filter(requested_by=user)

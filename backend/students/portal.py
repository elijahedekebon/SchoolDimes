"""Part 4A: the read-only student portal (school-issued student logins)."""
from django.db import transaction
from django.utils.translation import gettext as _

from accounts.models import User
from core.audit import audit
from core.exceptions import ServiceError

from .models import StudentAccount


def portal_account_for(student):
    return StudentAccount.objects.filter(student=student).select_related("user").first()


@transaction.atomic
def create_portal_account(actor, student, *, email, password):
    if portal_account_for(student) is not None:
        raise ServiceError("portal_account_exists", _("This student already has a portal login."), status=409)
    if User.objects.filter(email__iexact=email).exists():
        raise ServiceError("email_taken", _("An account with this email already exists."), status=409)
    user = User.objects.create_user(email=email, password=password, role=User.Role.STUDENT,
                                    school=student.school, full_name=student.name)
    account = StudentAccount.objects.create(user=user, student=student, created_by=actor)
    if actor is not None:
        audit(actor, "student.portal_account.create", student, force=True)
    return account


@transaction.atomic
def remove_portal_account(actor, student):
    account = portal_account_for(student)
    if account is None:
        raise ServiceError("not_found", _("This student has no portal login."), status=404)
    account.user.delete()  # cascades the link; the student's money and history are untouched
    audit(actor, "student.portal_account.remove", student, force=True)


def portal_summary(user):
    """Everything the student portal shows, for the signed-in student only."""
    from django.db.models import Q

    from content.models import FinancialLiteracyTip
    from pos.models import PosTransaction
    from wallets.models import SavingsGoal, Wallet
    from wallets.serializers import SavingsGoalSerializer

    account = getattr(user, "student_account", None)
    if user.role != User.Role.STUDENT or account is None:
        raise ServiceError("forbidden", _("Only student portal accounts can use this page."), status=403)
    student = account.student
    wallets = {w.wallet_type: w for w in Wallet.objects.filter(student=student, wallet_type__in=["main", "savings"])}
    goals = SavingsGoal.objects.filter(wallet__student=student)
    purchases = (PosTransaction.objects.filter(student=student).exclude(sync_status="rejected")
                 .select_related("device").prefetch_related("items").order_by("-device_local_timestamp")[:10])
    tip = (FinancialLiteracyTip.objects.filter(Q(school=student.school) | Q(school__isnull=True),
                                               language=user.preferred_language).order_by("?").first()
           or FinancialLiteracyTip.objects.filter(Q(school=student.school) | Q(school__isnull=True),
                                                  language="en").order_by("?").first())
    return {
        "student": {"id": student.pk, "name": student.name, "first_name": student.name.split(" ")[0],
                    "class_name": student.class_name},
        "school": {"id": student.school_id, "name": student.school.name, "branding": student.school.branding or {}},
        "main_balance": str(wallets["main"].balance) if "main" in wallets else "0.00",
        "savings_balance": str(wallets["savings"].balance) if "savings" in wallets else "0.00",
        "savings_goals": SavingsGoalSerializer(goals, many=True).data,
        "recent_purchases": [
            {"id": p.pk, "when": p.device_local_timestamp, "amount": str(p.amount), "place": p.device.device_name,
             "items": [{"description": i.description, "quantity": i.quantity, "line_total": str(i.line_total)}
                       for i in p.items.all()]}
            for p in purchases
        ],
        "tip": {"title": tip.title, "body": tip.body, "language": tip.language} if tip else None,
    }

"""Part 4A: the parent app's one-call dashboard."""
from decimal import Decimal

from django.db.models import Q

from accounts.models import GuardianVerification
from cards.models import Card
from content.models import FinancialLiteracyTip
from notifications.models import NotificationEvent
from notifications.services import get_preferences
from policies.services import get_effective_policy
from students.history import serialize_history
from students.models import Guardian
from wallets.models import LedgerEntry, SavingsGoal, Wallet
from wallets.savings import window_is_open
from wallets.serializers import SavingsGoalSerializer

RECENT = 5


def _current_card(cards):
    """The card the student uses now: the newest non-lost card, else the newest."""
    usable = [c for c in cards if c.status != Card.Status.LOST]
    pick = (usable or cards or [None])[0]
    return None if pick is None else {"id": pick.pk, "card_uid": pick.card_uid, "status": pick.status,
                                      "updated_at": pick.updated_at}


def parent_dashboard(user):
    links = list(Guardian.objects.filter(parent=user).select_related("student__school").order_by("student__name"))
    student_ids = [g.student_id for g in links]
    wallets = {(w.student_id, w.wallet_type): w for w in
               Wallet.objects.filter(student_id__in=student_ids, wallet_type__in=["main", "savings"])}
    cards = {}
    for c in Card.objects.filter(student_id__in=student_ids).order_by("-issued_at"):
        cards.setdefault(c.student_id, []).append(c)
    goals = {}
    for g in SavingsGoal.objects.filter(wallet__student_id__in=student_ids).select_related("wallet"):
        goals.setdefault(g.wallet.student_id, []).append(g)
    prefs = get_preferences(user).low_balance_thresholds or {}

    students = []
    for link in links:
        s = link.student
        main, savings = wallets.get((s.pk, "main")), wallets.get((s.pk, "savings"))
        custom = prefs.get(str(s.pk))
        threshold = Decimal(str(custom)) if custom is not None else get_effective_policy(s).low_balance_threshold
        recent = LedgerEntry.objects.filter(wallet__student=s, wallet__wallet_type__in=["main", "savings"]) \
            .select_related("wallet").order_by("-created_at", "-id")[:RECENT]
        students.append({
            "id": s.pk,
            "name": s.name,
            "first_name": s.name.split(" ")[0],
            "class_name": s.class_name,
            "photo_url": s.photo.url if s.photo else None,
            "school": {"id": s.school_id, "name": s.school.name, "branding": s.school.branding or {}},
            "relationship": link.relationship,
            "is_primary_contact": link.is_primary_contact,
            "main_wallet": None if main is None else {"id": main.pk, "balance": str(main.balance)},
            "savings_wallet": None if savings is None else {
                "id": savings.pk, "balance": str(savings.balance),
                "withdrawal_window_start": savings.withdrawal_window_start,
                "withdrawal_window_end": savings.withdrawal_window_end,
                "withdrawal_window_open": window_is_open(savings),
            },
            "savings_goals": SavingsGoalSerializer(goals.get(s.pk, []), many=True).data,
            "card": _current_card(cards.get(s.pk, [])),
            "low_balance_threshold": str(threshold),
            "is_low_balance": bool(main and main.balance < threshold),
            "recent_transactions": serialize_history(recent),
        })

    verification = GuardianVerification.objects.filter(parent=user).first()
    langs = [user.preferred_language, "en"]
    school_ids = {link.student.school_id for link in links}
    tip = None
    for lang in langs:
        tip = FinancialLiteracyTip.objects.filter(Q(school_id__in=school_ids) | Q(school__isnull=True),
                                                  language=lang).order_by("-created_at").first()
        if tip:
            break
    return {
        "user": {"id": user.pk, "email": user.email, "full_name": user.full_name, "phone_number": user.phone_number,
                 "preferred_language": user.preferred_language},
        "verification_status": verification.status if verification else None,
        "unread_notifications": NotificationEvent.objects.filter(user=user, channel="in_app", read_at__isnull=True).count(),
        "students": students,
        "tip": None if tip is None else {"id": tip.pk, "title": tip.title, "body": tip.body, "language": tip.language,
                                         "target_age_range": tip.target_age_range},
    }

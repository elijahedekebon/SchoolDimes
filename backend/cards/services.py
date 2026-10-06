import re
import uuid

from django.contrib.auth.hashers import check_password, make_password

from .models import Card


def generate_card_uid() -> str:
    return uuid.uuid4().hex


_UID_SEPARATORS = re.compile(r"[\s:\-]")
_UID_HEX = re.compile(r"^[0-9a-f]{8,64}$")


def normalize_card_uid(raw: str) -> str:
    """Part 4A: the one canonical card_uid format.

    An NFC tag UID is read as bytes (4, 7 or 10 for ISO 14443-A cards such as
    NTAG213/215 and MIFARE). It is stored as **lowercase hex, two digits per
    byte, in the order the reader returns the bytes (Android `Tag.getId()`
    order), with no separators**: bytes 04 A2 2B 7C 91 3E 80 -> "04a22b7c913e80".
    Input may use upper case, spaces, ':' or '-' between bytes. Server-generated
    UIDs (uuid4 hex, 32 chars) already match this format.
    Raises ValueError when the input isn't 4-32 whole bytes of hex.
    """
    uid = _UID_SEPARATORS.sub("", (raw or "").strip()).lower()
    if not _UID_HEX.match(uid) or len(uid) % 2:
        raise ValueError("card_uid must be 4-32 bytes of hex, e.g. 04:A2:2B:7C:91:3E:80")
    return uid


def hash_pin(raw_pin: str) -> str:
    """Card PINs use Django's pbkdf2_sha256 format, with CARD_PIN_HASH_ITERATIONS
    (default 40,000) instead of Django's 870,000: offline POS devices verify the
    hash on cheap phones while a student waits, and for a 4-6 digit PIN the
    iteration count adds little -- lockout and device revocation are the real
    protection (DECISIONS.md, Part 3). Devices read the iteration count from each
    hash, so older 870k hashes keep working until the PIN is reset."""
    from django.conf import settings
    from django.contrib.auth.hashers import PBKDF2PasswordHasher

    hasher = PBKDF2PasswordHasher()
    return hasher.encode(raw_pin, hasher.salt(), iterations=settings.CARD_PIN_HASH_ITERATIONS)


def verify_pin(card: Card, raw_pin: str) -> bool:
    # Card PINs are always pbkdf2_sha256 (see hash_pin), whatever
    # PASSWORD_HASHERS says for user passwords; older hashes fall back.
    from django.contrib.auth.hashers import PBKDF2PasswordHasher

    if card.pin_hash.startswith("pbkdf2_sha256$"):
        return PBKDF2PasswordHasher().verify(raw_pin, card.pin_hash)
    return check_password(raw_pin, card.pin_hash)


def issue_card(student, raw_pin: str, card_uid: str | None = None) -> Card:
    return Card.objects.create(
        school=student.school,
        student=student,
        card_uid=card_uid or generate_card_uid(),
        pin_hash=hash_pin(raw_pin),
        status=Card.Status.ACTIVE,
    )


def reissue_card(old_card: Card, raw_pin: str, card_uid: str | None = None) -> Card:
    """Retires `old_card` (marks it lost) and issues a fresh one for the
    same student. Used for lost/damaged cards."""
    old_card.status = Card.Status.LOST
    old_card.save(update_fields=["status", "updated_at"])
    return issue_card(old_card.student, raw_pin, card_uid=card_uid)


def reset_card_pin(card: Card, raw_pin: str) -> Card:
    """Part 4A: an admin sets a new PIN (e.g. the student forgot it). The raw
    PIN is hashed immediately and never stored or returned. `updated_at`
    changes, so POS devices pick up the new hash on their next incremental
    cache refresh. Does not unfreeze a card frozen by PIN lockout -- unfreeze
    is a separate, deliberate step."""
    card.pin_hash = hash_pin(raw_pin)
    card.save(update_fields=["pin_hash", "updated_at"])
    return card


def freeze_card(card: Card) -> Card:
    card.status = Card.Status.FROZEN
    card.save(update_fields=["status", "updated_at"])
    return card


def unfreeze_card(card: Card) -> Card:
    card.status = Card.Status.ACTIVE
    card.save(update_fields=["status", "updated_at"])
    return card


def report_lost_card(card: Card) -> Card:
    card.status = Card.Status.LOST
    card.save(update_fields=["status", "updated_at"])
    return card


def card_status_changed(card: Card, actor, event_type: str):
    """Part 2: notify the student's other guardians (not the actor) and
    audit-log platform_admin actions."""
    from core.audit import audit
    from notifications.services import notify_guardians

    audit(actor, event_type, card)
    notify_guardians(
        card.student,
        event_type,
        {
            "card_id": card.pk,
            "student_id": card.student_id,
            "student_name": card.student.name,
            "actor_name": actor.full_name or actor.email,
        },
        exclude_user_ids=[actor.pk],
    )



# ---------------------------------------------------------------------------
# Shared by the API viewset and the web pages
# ---------------------------------------------------------------------------

def cards_for(user, params):
    """GET /cards/: ?student=, ?status=, ?card_uid= (normalised); platform_admin
    all (?school=), parents their children's cards, staff their school's."""
    from core.permissions import is_platform_admin

    qs = Card.objects.select_related("student", "school")
    if params.get("student"):
        qs = qs.filter(student_id=params["student"])
    if params.get("status"):
        qs = qs.filter(status=params["status"])
    if params.get("card_uid"):
        try:
            qs = qs.filter(card_uid=normalize_card_uid(params["card_uid"]))
        except ValueError:
            qs = qs.none()
    if is_platform_admin(user):
        return qs.filter(school_id=params["school"]) if params.get("school") else qs
    if user.role == "parent":
        return qs.filter(student__guardian_links__parent=user).distinct()
    return qs.filter(school_id=user.school_id)


def freeze_card_by(actor, card: Card) -> Card:
    """Freeze + notify the other guardians + audit (platform_admin). Takes
    effect for authorize_debit() at once; offline devices on their next refresh."""
    freeze_card(card)
    card_status_changed(card, actor, "card_frozen")
    return card


def unfreeze_card_by(actor, card: Card) -> Card:
    from django.utils.translation import gettext as _

    from core.exceptions import ServiceError

    if card.status == Card.Status.LOST:
        # Part 2: a lost card is replaced via reissue, never reactivated.
        raise ServiceError("card_lost", _("A lost card cannot be unfrozen; reissue it instead."), status=409)
    unfreeze_card(card)
    card_status_changed(card, actor, "card_unfrozen")
    return card


def report_lost_by(actor, card: Card) -> Card:
    report_lost_card(card)
    card_status_changed(card, actor, "card_reported_lost")
    return card


def reset_pin_by(actor, card: Card, raw_pin) -> Card:
    from django.utils.translation import gettext as _

    from core.audit import audit
    from core.exceptions import ServiceError

    if card.status == Card.Status.LOST:
        raise ServiceError("card_lost", _("A lost card can't get a new PIN; reissue it instead."), status=409)
    reset_card_pin(card, raw_pin)
    audit(actor, "card.reset_pin", card)
    return card

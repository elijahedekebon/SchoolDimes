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
    return make_password(raw_pin)


def verify_pin(card: Card, raw_pin: str) -> bool:
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

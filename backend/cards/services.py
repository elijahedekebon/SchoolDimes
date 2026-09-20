import uuid

from django.contrib.auth.hashers import check_password, make_password

from .models import Card


def generate_card_uid() -> str:
    return uuid.uuid4().hex


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


def freeze_card(card: Card) -> Card:
    card.status = Card.Status.FROZEN
    card.save(update_fields=["status", "updated_at"])
    return card


def unfreeze_card(card: Card) -> Card:
    card.status = Card.Status.ACTIVE
    card.save(update_fields=["status", "updated_at"])
    return card

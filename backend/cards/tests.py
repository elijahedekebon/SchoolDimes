import pytest

from cards.models import Card
from cards.services import freeze_card, issue_card, reissue_card, unfreeze_card, verify_pin


@pytest.mark.django_db
class TestCardPinHashing:
    def test_pin_is_hashed_not_stored_raw(self, student_a1):
        card = issue_card(student_a1, "4321")
        assert card.pin_hash != "4321"
        assert verify_pin(card, "4321") is True
        assert verify_pin(card, "0000") is False

    def test_reissue_retires_old_card_and_creates_new_one(self, student_a1):
        old_card = issue_card(student_a1, "1111")
        new_card = reissue_card(old_card, "2222")

        old_card.refresh_from_db()
        assert old_card.status == Card.Status.LOST
        assert new_card.status == Card.Status.ACTIVE
        assert new_card.card_uid != old_card.card_uid
        assert verify_pin(new_card, "2222") is True

    def test_freeze_and_unfreeze(self, card_a1):
        freeze_card(card_a1)
        card_a1.refresh_from_db()
        assert card_a1.status == Card.Status.FROZEN

        unfreeze_card(card_a1)
        card_a1.refresh_from_db()
        assert card_a1.status == Card.Status.ACTIVE

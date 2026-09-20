import pytest

from tenants.models import School, SchoolReferral
from tenants.services import apply_referral_reward


@pytest.mark.django_db
class TestSchoolReferral:
    def test_create_referral(self, school_a, school_b):
        referral = SchoolReferral.objects.create(
            referring_school=school_a, referred_school=school_b
        )
        assert referral.status == SchoolReferral.Status.PENDING
        assert referral.reward_applied is False

    def test_apply_referral_reward(self, school_a, school_b):
        referral = SchoolReferral.objects.create(
            referring_school=school_a, referred_school=school_b
        )
        apply_referral_reward(referral)
        referral.refresh_from_db()
        assert referral.status == SchoolReferral.Status.APPLIED
        assert referral.reward_applied is True

    def test_school_cannot_refer_itself(self, school_a):
        from django.db import IntegrityError, transaction

        with pytest.raises(IntegrityError):
            with transaction.atomic():
                SchoolReferral.objects.create(referring_school=school_a, referred_school=school_a)

    def test_school_crud(self):
        school = School.objects.create(name="Test School", supported_languages=["en", "lg"])
        school.name = "Renamed School"
        school.save()
        school.refresh_from_db()
        assert school.name == "Renamed School"
        assert school.supported_languages == ["en", "lg"]

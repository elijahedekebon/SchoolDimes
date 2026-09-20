import pytest
from django.contrib.auth.hashers import check_password

from accounts.models import GuardianVerification, User
from accounts.services import mark_guardian_verification


@pytest.mark.django_db
class TestUserModel:
    def test_password_is_hashed(self):
        user = User.objects.create_user(
            email="hash-check@schooldimes.test", password="pw123456", role=User.Role.PARENT
        )
        assert user.password != "pw123456"
        assert check_password("pw123456", user.password)

    def test_platform_admin_can_have_no_school(self, platform_admin):
        assert platform_admin.school is None
        assert platform_admin.role == User.Role.PLATFORM_ADMIN


@pytest.mark.django_db
class TestGuardianVerification:
    def test_verification_lifecycle(self, parent_user):
        verification = GuardianVerification.objects.create(
            parent=parent_user,
            full_name="Jane Parent",
            id_number="CM123456789",
        )
        assert verification.status == GuardianVerification.Status.PENDING
        assert verification.verified_at is None

        mark_guardian_verification(verification, status=GuardianVerification.Status.VERIFIED)
        verification.refresh_from_db()
        assert verification.status == GuardianVerification.Status.VERIFIED
        assert verification.verified_at is not None

    def test_one_verification_per_parent(self, parent_user):
        GuardianVerification.objects.create(
            parent=parent_user, full_name="Jane Parent", id_number="CM123456789"
        )
        with pytest.raises(Exception):
            GuardianVerification.objects.create(
                parent=parent_user, full_name="Jane Parent", id_number="CM999999999"
            )

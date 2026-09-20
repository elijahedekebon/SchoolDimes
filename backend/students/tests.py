import pytest

from students.models import Guardian
from wallets.views import wallets_visible_to


@pytest.mark.django_db
class TestGuardianStudentRelations:
    def test_parent_sees_only_their_own_linked_students(
        self, parent_user, student_a1, student_a2, student_b1
    ):
        Guardian.objects.create(parent=parent_user, student=student_a1)

        linked_ids = set(
            Guardian.objects.filter(parent=parent_user).values_list("student_id", flat=True)
        )
        assert linked_ids == {student_a1.id}
        assert student_a2.id not in linked_ids
        assert student_b1.id not in linked_ids

    def test_siblings_can_share_one_guardian(self, parent_user, student_a1, student_a2):
        Guardian.objects.create(parent=parent_user, student=student_a1)
        Guardian.objects.create(parent=parent_user, student=student_a2)

        linked = Guardian.objects.filter(parent=parent_user).values_list("student_id", flat=True)
        assert set(linked) == {student_a1.id, student_a2.id}

    def test_student_can_have_multiple_guardians(self, parent_user, school_a, student_a1):
        from accounts.models import User

        second_parent = User.objects.create_user(
            email="second-parent@schooldimes.test", password="pw123456", role=User.Role.PARENT
        )
        Guardian.objects.create(parent=parent_user, student=student_a1)
        Guardian.objects.create(parent=second_parent, student=student_a1)

        guardians = Guardian.objects.filter(student=student_a1).values_list("parent_id", flat=True)
        assert set(guardians) == {parent_user.id, second_parent.id}

    def test_duplicate_guardian_link_is_rejected(self, parent_user, student_a1):
        from django.db import IntegrityError

        Guardian.objects.create(parent=parent_user, student=student_a1)
        with pytest.raises(IntegrityError):
            Guardian.objects.create(parent=parent_user, student=student_a1)


@pytest.mark.django_db
class TestTenantIsolation:
    def test_wallets_visible_to_school_admin_excludes_other_schools(
        self, school_admin_a, student_a1, student_b1
    ):
        from wallets.models import Wallet

        wallet_a = Wallet.objects.create(
            school=student_a1.school, student=student_a1, wallet_type=Wallet.WalletType.MAIN
        )
        Wallet.objects.create(
            school=student_b1.school, student=student_b1, wallet_type=Wallet.WalletType.MAIN
        )

        visible = wallets_visible_to(school_admin_a)
        assert list(visible) == [wallet_a]

    def test_wallets_visible_to_parent_only_their_students(
        self, parent_user, student_a1, student_b1
    ):
        from wallets.models import Wallet

        Guardian.objects.create(parent=parent_user, student=student_a1)
        wallet_a = Wallet.objects.create(
            school=student_a1.school, student=student_a1, wallet_type=Wallet.WalletType.MAIN
        )
        Wallet.objects.create(
            school=student_b1.school, student=student_b1, wallet_type=Wallet.WalletType.MAIN
        )

        visible = wallets_visible_to(parent_user)
        assert list(visible) == [wallet_a]

    def test_platform_admin_sees_all_schools(self, platform_admin, student_a1, student_b1):
        from wallets.models import Wallet

        Wallet.objects.create(
            school=student_a1.school, student=student_a1, wallet_type=Wallet.WalletType.MAIN
        )
        Wallet.objects.create(
            school=student_b1.school, student=student_b1, wallet_type=Wallet.WalletType.MAIN
        )
        assert wallets_visible_to(platform_admin).count() == 2

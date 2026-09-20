import pytest

from accounts.models import User
from cards.services import issue_card
from students.models import Guardian, Student
from tenants.models import School
from wallets.models import Wallet


@pytest.fixture
def school_a(db):
    return School.objects.create(name="Kampala Primary School")


@pytest.fixture
def school_b(db):
    return School.objects.create(name="Jinja Junior School")


@pytest.fixture
def platform_admin(db):
    return User.objects.create_user(
        email="platform-admin@schooldimes.test",
        password="pw123456",
        role=User.Role.PLATFORM_ADMIN,
    )


@pytest.fixture
def school_admin_a(db, school_a):
    return User.objects.create_user(
        email="admin-a@schooldimes.test",
        password="pw123456",
        role=User.Role.SCHOOL_ADMIN,
        school=school_a,
    )


@pytest.fixture
def school_admin_b(db, school_b):
    return User.objects.create_user(
        email="admin-b@schooldimes.test",
        password="pw123456",
        role=User.Role.SCHOOL_ADMIN,
        school=school_b,
    )


@pytest.fixture
def parent_user(db):
    return User.objects.create_user(
        email="parent@schooldimes.test",
        password="pw123456",
        role=User.Role.PARENT,
    )


@pytest.fixture
def student_a1(db, school_a):
    return Student.objects.create(school=school_a, name="Amina N.", class_name="P4")


@pytest.fixture
def student_a2(db, school_a):
    return Student.objects.create(school=school_a, name="Brian K.", class_name="P4")


@pytest.fixture
def student_b1(db, school_b):
    return Student.objects.create(school=school_b, name="Cynthia M.", class_name="S1")


@pytest.fixture
def guardian_link_a1(db, parent_user, student_a1):
    return Guardian.objects.create(parent=parent_user, student=student_a1)


def make_wallet(student, wallet_type):
    return Wallet.objects.create(school=student.school, student=student, wallet_type=wallet_type)


@pytest.fixture
def main_wallet_a1(db, student_a1):
    return make_wallet(student_a1, Wallet.WalletType.MAIN)


@pytest.fixture
def savings_wallet_a1(db, student_a1):
    return make_wallet(student_a1, Wallet.WalletType.SAVINGS)


@pytest.fixture
def card_a1(db, student_a1):
    return issue_card(student_a1, "1234")

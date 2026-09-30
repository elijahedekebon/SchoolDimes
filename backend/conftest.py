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


# ---------------------------------------------------------------------------
# Part 2 shared fixtures & helpers
# ---------------------------------------------------------------------------
from decimal import Decimal  # noqa: E402

from rest_framework.test import APIClient  # noqa: E402


@pytest.fixture(autouse=True)
def _part2_test_settings(settings):
    """Local-memory cache (no Redis needed) and inline Celery for every test."""
    from django.core.cache import cache

    from config.celery import app as celery_app

    settings.CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
    # PBKDF2 at 870k iterations per user/PIN makes the suite crawl; tests
    # only need *a* salted hash. Production keeps Django's default.
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]
    settings.AGGREGATOR_MODE = "mock"
    settings.PAYMENT_AGGREGATOR_WEBHOOK_SECRET = "test-webhook-secret"
    celery_app.conf.task_always_eager = True
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def api_client():
    return APIClient()


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


@pytest.fixture
def parent_client(parent_user):
    return client_for(parent_user)


@pytest.fixture
def admin_a_client(school_admin_a):
    return client_for(school_admin_a)


@pytest.fixture
def admin_b_client(school_admin_b):
    return client_for(school_admin_b)


@pytest.fixture
def other_parent(db):
    return User.objects.create_user(
        email="other-parent@schooldimes.test", password="pw123456", role=User.Role.PARENT
    )


@pytest.fixture
def funded_student_a1(db, student_a1, guardian_link_a1):
    """student_a1 with main+savings wallets, an active card (PIN 1234) and
    10,000 UGX deposited through the balanced deposit path."""
    from wallets.services import ensure_student_wallets

    main, _savings = ensure_student_wallets(student_a1)
    issue_card(student_a1, "1234")
    fund_wallet(main, "10000")
    return student_a1


def fund_wallet(wallet, amount):
    """Credits a wallet the way a confirmed deposit does (clearing -> wallet)."""
    from wallets.models import LedgerEntry
    from wallets.services import get_system_wallet, post_transfer

    clearing = get_system_wallet(wallet.school_id, Wallet.WalletType.AGGREGATOR_CLEARING)
    post_transfer(
        debit_wallet=clearing,
        credit_wallet=wallet,
        amount=Decimal(amount),
        entry_type=LedgerEntry.EntryType.DEPOSIT,
        reference_id=f"test-fund:{wallet.pk}",
    )
    wallet.refresh_from_db()
    return wallet


def assert_books_balanced(*schools):
    """Every wallet's cached balance equals its ledger re-sum, every ledger
    reference nets to zero, and each school's wallets sum to exactly zero."""
    from django.db.models import Sum

    from wallets.models import LedgerEntry
    from wallets.services import compute_balance, school_books_total

    for school in schools:
        for wallet in Wallet.objects.filter(school=school):
            assert wallet.cached_balance == compute_balance(wallet), wallet
        assert school_books_total(school) == Decimal("0"), school
        for ref in (
            LedgerEntry.objects.filter(school=school)
            .exclude(reference_id="")
            .values_list("reference_id", flat=True)
            .distinct()
        ):
            entries = LedgerEntry.objects.filter(school=school, reference_id=ref)
            credits = entries.filter(direction="credit").aggregate(s=Sum("amount"))["s"] or 0
            debits = entries.filter(direction="debit").aggregate(s=Sum("amount"))["s"] or 0
            assert credits == debits, ref

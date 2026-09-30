from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from accounts.models import GuardianVerification, User
from accounts.services import mark_guardian_verification
from cards.services import issue_card
from content.models import FinancialLiteracyTip
from students.models import Guardian, Student
from tenants.models import School, SchoolReferral
from wallets.models import LedgerEntry, SavingsGoal, Wallet
from wallets.services import get_system_wallet, post_transfer

from ._seed_part2 import seed_part2


class Command(BaseCommand):
    help = "Seeds demo data: two schools, a referral, admins/parents/students, cards, wallets, and tips."

    @transaction.atomic
    def handle(self, *args, **options):
        school_a, _ = School.objects.get_or_create(
            name="Kampala Demo Primary School",
            defaults={
                "address": "Plot 12, Ntinda Road, Kampala",
                "supported_languages": ["en", "lg"],
                "branding": {"primary_color": "#1F6FEB"},
            },
        )
        school_b, _ = School.objects.get_or_create(
            name="Jinja Demo Secondary School",
            defaults={
                "address": "Main Street, Jinja",
                "supported_languages": ["en", "sw"],
                "branding": {"primary_color": "#2EA043"},
            },
        )
        SchoolReferral.objects.get_or_create(referring_school=school_a, referred_school=school_b)
        self.stdout.write(self.style.SUCCESS(f"Schools ready: {school_a}, {school_b}"))

        school_admin, created = User.objects.get_or_create(
            email="admin@kampaladps.schooldimes.test",
            defaults={"role": User.Role.SCHOOL_ADMIN, "school": school_a, "full_name": "Grace Admin"},
        )
        if created:
            school_admin.set_password("pw123456")
            school_admin.save()

        parent1, created = User.objects.get_or_create(
            email="parent1@schooldimes.test",
            defaults={"role": User.Role.PARENT, "full_name": "Moses Parent", "preferred_language": "en"},
        )
        if created:
            parent1.set_password("pw123456")
            parent1.save()

        parent2, created = User.objects.get_or_create(
            email="parent2@schooldimes.test",
            defaults={"role": User.Role.PARENT, "full_name": "Sarah Parent", "preferred_language": "lg"},
        )
        if created:
            parent2.set_password("pw123456")
            parent2.save()

        verification, _ = GuardianVerification.objects.get_or_create(
            parent=parent1,
            defaults={"full_name": "Moses Parent", "id_number": "CM90210001XY"},
        )
        if verification.status != GuardianVerification.Status.VERIFIED:
            mark_guardian_verification(verification, status=GuardianVerification.Status.VERIFIED)
        self.stdout.write(self.style.SUCCESS("Parents ready (parent1 verified, parent2 unverified)"))

        student1, _ = Student.objects.get_or_create(
            school=school_a, name="Amina Nakato", defaults={"class_name": "P4"}
        )
        student2, _ = Student.objects.get_or_create(
            school=school_a, name="Brian Nakato", defaults={"class_name": "P2"}
        )
        student3, _ = Student.objects.get_or_create(
            school=school_a, name="Cynthia Auma", defaults={"class_name": "P6"}
        )
        # siblings sharing a guardian
        Guardian.objects.get_or_create(
            parent=parent1, student=student1, defaults={"relationship": Guardian.Relationship.MOTHER}
        )
        Guardian.objects.get_or_create(
            parent=parent1, student=student2, defaults={"relationship": Guardian.Relationship.MOTHER}
        )
        Guardian.objects.get_or_create(
            parent=parent2, student=student3, defaults={"relationship": Guardian.Relationship.MOTHER}
        )
        self.stdout.write(self.style.SUCCESS("Students + guardian links ready"))

        for i, student in enumerate([student1, student2, student3], start=1):
            if not student.cards.exists():
                issue_card(student, f"100{i}")

            main_wallet, _ = Wallet.objects.get_or_create(
                school=student.school, student=student, wallet_type=Wallet.WalletType.MAIN
            )
            savings_wallet, _ = Wallet.objects.get_or_create(
                school=student.school, student=student, wallet_type=Wallet.WalletType.SAVINGS
            )

            if not main_wallet.ledger_entries.exists():
                # Part 2: every seeded movement is a balanced transfer.
                clearing = get_system_wallet(student.school, Wallet.WalletType.AGGREGATOR_CLEARING)
                settlement = get_system_wallet(student.school, Wallet.WalletType.SCHOOL_SETTLEMENT)
                post_transfer(
                    debit_wallet=clearing,
                    credit_wallet=main_wallet,
                    amount=Decimal("20000"),
                    entry_type=LedgerEntry.EntryType.DEPOSIT,
                    reference_id=f"seed:{student.pk}:deposit",
                    description="Initial parent top-up",
                )
                post_transfer(
                    debit_wallet=main_wallet,
                    credit_wallet=settlement,
                    amount=Decimal("3500"),
                    entry_type=LedgerEntry.EntryType.POS_PURCHASE,
                    reference_id=f"seed:{student.pk}:lunch",
                    description="Canteen lunch",
                )
                post_transfer(
                    debit_wallet=main_wallet,
                    credit_wallet=savings_wallet,
                    amount=Decimal("2000"),
                    entry_type=LedgerEntry.EntryType.SAVINGS_MOVE_OUT,
                    credit_entry_type=LedgerEntry.EntryType.SAVINGS_MOVE_IN,
                    reference_id=f"seed:{student.pk}:savings",
                    description="Moved to savings goal",
                )

            SavingsGoal.objects.get_or_create(
                wallet=savings_wallet,
                goal_name="New bicycle",
                defaults={"target_amount": Decimal("50000")},
            )

        self.stdout.write(self.style.SUCCESS("Cards, wallets, ledger entries, and savings goals ready"))

        tips = [
            ("en", "Save a little, often", "Putting aside even small amounts regularly adds up over time."),
            ("en", "Needs vs. wants", "Before buying a snack, ask: do I need this, or just want it?"),
            ("lg", "Terekera katono buli kiseera", "Okuterekera ensimbi entono buli kiseera kikuyamba mu biseera eby'omunyuma."),
            ("sw", "Weka akiba kidogo mara kwa mara", "Kuweka pesa kidogo mara kwa mara kunasaidia kuwa na akiba kubwa baadaye."),
        ]
        for language, title, body in tips:
            FinancialLiteracyTip.objects.get_or_create(
                title=title, language=language, defaults={"body": body}
            )
        self.stdout.write(self.style.SUCCESS("Financial literacy tips ready (en x2, lg x1, sw x1)"))

        # Part 2: payments, policy, POS, merchants, fees, pooled funds, disputes...
        seed_part2(self.stdout, self.style, school_a, school_admin, parent1, parent2, [student1, student2, student3])

        self.stdout.write(self.style.SUCCESS("Demo seed complete."))

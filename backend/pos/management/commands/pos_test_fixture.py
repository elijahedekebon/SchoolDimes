"""Part 3: a known fixture for the POS app's integration tests (dev only).

    docker compose exec web python manage.py pos_test_fixture [--balance 20000]

Creates a fresh "POS E2E Student <n>" (random 7-byte card UID, PIN 2468) in
the demo school -- fresh, so daily caps start at zero on every run -- funds
the main wallet with --balance through a balanced
clearing -> wallet transfer (like a confirmed deposit), registers a fresh
canteen and attendance device, and prints JSON with the raw tokens.
"""
import json
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from cards.services import issue_card
from pos.services import register_device
from students.models import Student
from tenants.models import School
from wallets.models import LedgerEntry, Wallet
from wallets.services import ensure_student_wallets, get_system_wallet, post_transfer

PIN = "2468"


class Command(BaseCommand):
    help = "Dev only: POS integration-test fixture (student, card, tokens)."

    def add_arguments(self, parser):
        parser.add_argument("--balance", default="20000")

    def handle(self, *args, **opts):
        if not settings.DEBUG:
            raise CommandError("pos_test_fixture only runs with DEBUG=True.")
        school = School.objects.order_by("pk").first()
        if school is None:
            raise CommandError("Run seed_demo first.")
        import secrets

        n = Student.objects.filter(name__startswith="POS E2E Student").count() + 1
        student = Student.objects.create(school=school, name=f"POS E2E Student {n}", class_name="P5")
        main, _savings = ensure_student_wallets(student)
        uid = "04" + secrets.token_hex(6)
        issue_card(student, PIN, card_uid=uid)
        target = Decimal(opts["balance"])
        main.refresh_from_db()
        if main.cached_balance < target:
            post_transfer(
                debit_wallet=get_system_wallet(school, Wallet.WalletType.AGGREGATOR_CLEARING),
                credit_wallet=main,
                amount=target - main.cached_balance,
                entry_type=LedgerEntry.EntryType.DEPOSIT,
                reference_id=f"e2e-topup:{main.pk}",
                description="POS integration-test top-up",
            )
        canteen, canteen_token = register_device(None, school=school, device_name="E2E canteen", device_role="canteen")
        gate, gate_token = register_device(None, school=school, device_name="E2E gate", device_role="attendance")
        main.refresh_from_db()
        self.stdout.write(json.dumps({
            "school_id": school.pk, "student_id": student.pk, "card_uid": uid, "pin": PIN,
            "balance": str(main.cached_balance), "canteen_token": canteen_token, "attendance_token": gate_token,
        }))

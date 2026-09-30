"""
Part 2: make Part 1's single-sided ledger history double-entry.

Part 1 (seed_demo) posted deposits and POS purchases on student wallets with
no counter-entry. This migration APPENDS the missing other side -- nothing
is edited or deleted:
  deposit / gift_voucher credit on a student wallet -> debit aggregator_clearing
  pos_purchase / fee_payment debit on a student wallet -> credit school_settlement
Savings moves were already posted in pairs by Part 1 and are left alone.
Each counter-entry carries reference_id "legacy:<original entry id>", which
also makes this migration safe to re-run.

This is the ONE place that writes LedgerEntry rows without calling
post_ledger_entry(): migrations must use historical models, and the service
imports live models. It replicates post_ledger_entry()'s bookkeeping exactly
(append entry, adjust cached_balance) under the migration's transaction.
"""
from django.db import migrations

CREDIT_TYPES = ("deposit", "gift_voucher")
DEBIT_TYPES = ("pos_purchase", "fee_payment")


def forwards(apps, schema_editor):
    Wallet = apps.get_model("wallets", "Wallet")
    LedgerEntry = apps.get_model("wallets", "LedgerEntry")

    legacy = LedgerEntry.objects.filter(
        wallet__wallet_type__in=["main", "savings"]
    ).exclude(reference_id__startswith="legacy:").order_by("pk")

    for entry in legacy:
        if entry.direction == "credit" and entry.entry_type in CREDIT_TYPES:
            system_type, direction, delta = "aggregator_clearing", "debit", -entry.amount
        elif entry.direction == "debit" and entry.entry_type in DEBIT_TYPES:
            system_type, direction, delta = "school_settlement", "credit", entry.amount
        else:
            continue
        reference = f"legacy:{entry.pk}"
        if LedgerEntry.objects.filter(reference_id=reference).exists():
            continue
        system_wallet, _ = Wallet.objects.get_or_create(
            school_id=entry.school_id, wallet_type=system_type, student=None
        )
        LedgerEntry.objects.create(
            school_id=entry.school_id,
            wallet=system_wallet,
            amount=entry.amount,
            direction=direction,
            entry_type=entry.entry_type,
            reference_id=reference,
            description="Part 1 legacy counter-entry",
        )
        system_wallet.cached_balance += delta
        system_wallet.save(update_fields=["cached_balance", "updated_at"])


class Migration(migrations.Migration):
    dependencies = [("wallets", "0002_system_wallets")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

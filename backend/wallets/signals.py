from django.dispatch import Signal

# Sent by post_ledger_entry() right after an entry is written, still inside
# the caller's transaction. kwargs: entry (LedgerEntry), balance_after
# (Decimal). Receivers that do I/O must defer it with transaction.on_commit.
ledger_entry_posted = Signal()

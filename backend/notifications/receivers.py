"""Signal receivers that turn ledger movements into notifications."""
from django.dispatch import receiver

from wallets.signals import ledger_entry_posted


@receiver(ledger_entry_posted)
def _savings_goal_reached(sender, entry, balance_after, **kwargs):
    wallet = entry.wallet
    if entry.direction != "credit" or wallet.wallet_type != "savings":
        return
    from wallets.savings import check_goals_reached

    # Runs inside the posting transaction, so it rolls back with the money
    # movement; notify() itself defers SMS/push I/O until commit.
    check_goals_reached(wallet)

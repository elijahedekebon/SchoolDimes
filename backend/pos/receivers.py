from django.dispatch import receiver

from payments.models import Deposit
from payments.signals import deposit_confirmed


@receiver(deposit_confirmed)
def _recover_on_topup(sender, deposit, **kwargs):
    """recover_from_next_topup / charge_guardian: every confirmed top-up of
    a student's main wallet pays down that student's pending shortfalls."""
    if deposit.purpose == Deposit.Purpose.WALLET_TOPUP and deposit.wallet.wallet_type == "main":
        from .services import recover_shortfalls

        recover_shortfalls(deposit.wallet)

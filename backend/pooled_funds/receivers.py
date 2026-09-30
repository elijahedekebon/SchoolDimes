from django.dispatch import receiver

from payments.models import Deposit
from payments.signals import deposit_confirmed


@receiver(deposit_confirmed)
def _on_deposit_confirmed(sender, deposit, **kwargs):
    if deposit.purpose == Deposit.Purpose.POOLED_FUND_CONTRIBUTION:
        from .services import record_contribution

        record_contribution(deposit)

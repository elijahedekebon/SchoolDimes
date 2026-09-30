from django.dispatch import Signal

# Sent inside the confirming transaction after a Deposit has been credited.
# kwargs: deposit. Pooled funds (contribution log) and POS (shortfall
# recovery) listen to this, which keeps `payments` independent of them.
deposit_confirmed = Signal()

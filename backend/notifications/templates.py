"""
Translatable notification templates, keyed by event_type.

Every string goes through gettext_lazy and is rendered inside
translation.override(recipient.preferred_language) -- see services.notify().
Placeholders use %(name)s and are filled from the event payload; a missing
key renders as an empty string rather than raising.
"""
from django.utils.translation import gettext_lazy as _

TEMPLATES = {
    # --- payments ---
    "deposit_confirmed": (
        _("Top-up received"),
        _("%(amount)s UGX was added to %(student_name)s's wallet."),
    ),
    "deposit_failed": (
        _("Top-up failed"),
        _("Your top-up of %(amount)s UGX for %(student_name)s did not go through: %(reason_label)s"),
    ),
    "contributor_topup_received": (
        _("Top-up from %(contributor_name)s"),
        _("%(contributor_name)s added %(amount)s UGX to %(student_name)s's wallet."),
    ),
    "gift_received": (
        _("A gift for %(student_name)s"),
        _('%(sender_name)s sent %(student_name)s a gift of %(amount)s UGX: "%(message)s"'),
    ),
    "recurring_topup_executed": (
        _("Scheduled top-up done"),
        _("Your scheduled top-up of %(amount)s UGX for %(student_name)s was completed."),
    ),
    "recurring_topup_failed": (
        _("Scheduled top-up failed"),
        _("Your scheduled top-up of %(amount)s UGX for %(student_name)s failed: %(reason_label)s"),
    ),
    "recurring_topup_paused": (
        _("Scheduled top-up paused"),
        _(
            "Your scheduled top-up for %(student_name)s was paused after %(failures)s failed "
            "attempts. Update it in the app to resume."
        ),
    ),
    # --- wallets ---
    "low_balance": (
        _("Low balance"),
        _(
            "%(student_name)s's balance is %(balance)s UGX, below your alert level of "
            "%(threshold)s UGX. Tap to top up."
        ),
    ),
    "savings_goal_reached": (
        _("Savings goal reached!"),
        _("%(student_name)s reached the savings goal \"%(goal_name)s\" (%(target_amount)s UGX)."),
    ),
    "savings_withdrawal_completed": (
        _("Savings withdrawal sent"),
        _("%(amount)s UGX from %(student_name)s's savings was sent to %(phone_number)s."),
    ),
    "savings_withdrawal_failed": (
        _("Savings withdrawal failed"),
        _(
            "The withdrawal of %(amount)s UGX from %(student_name)s's savings failed and the "
            "money was returned to savings: %(reason_label)s"
        ),
    ),
    "card_frozen": (
        _("Card frozen"),
        _("%(student_name)s's card was frozen by %(actor_name)s. No payments can be made with it."),
    ),
    "card_unfrozen": (
        _("Card unfrozen"),
        _("%(student_name)s's card was unfrozen by %(actor_name)s."),
    ),
    "card_reported_lost": (
        _("Card reported lost"),
        _("%(student_name)s's card was reported lost by %(actor_name)s. Ask the school for a new card."),
    ),
    "card_locked_pin_failures": (
        _("Card locked"),
        _("%(student_name)s's card was frozen after %(failures)s wrong PIN attempts."),
    ),
    "p2p_transfer_received": (
        _("Money received"),
        _("%(student_name)s received %(amount)s UGX from %(sender_name)s."),
    ),
    # --- school admin ---
    "p2p_alert_raised": (
        _("Transfer pattern alert"),
        _("Review needed: %(student_name)s — %(rule_label)s."),
    ),
    "shortfall_flagged": (
        _("POS shortfall flagged"),
        _(
            "An offline sale on %(student_name)s's card was short by %(shortfall_amount)s UGX "
            "(device %(device_name)s). Please review."
        ),
    ),
    "pos_transaction_flagged": (
        _("POS sale flagged"),
        _("An offline sale on %(student_name)s's card broke a rule (%(flags_label)s). Please review."),
    ),
    # --- disputes ---
    "dispute_status_changed": (
        _("Dispute update"),
        _("Your dispute #%(dispute_id)s is now: %(status_label)s. %(notes)s"),
    ),
    # --- attendance ---
    "attendance_tap_in": (
        _("Arrived at school"),
        _("%(student_name)s tapped in at %(time)s."),
    ),
    # --- privacy ---
    "data_request_updated": (
        _("Data request update"),
        _("Your %(request_type_label)s request #%(request_id)s is now %(status_label)s."),
    ),
    # --- pooled funds ---
    "pooled_fund_contribution_confirmed": (
        _("Contribution received"),
        _("Your contribution of %(amount)s UGX to \"%(fund_title)s\" was received."),
    ),
}

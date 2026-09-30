"""
Approved Part 1 conflict #4: the Policy model supersedes the Part 1
School.policy_defaults JSON. Copy any recognised scalar keys into each
school's default Policy row. The JSON field itself is left untouched (still
in the /schools/ API) but is no longer read by any Part 2 code.

Category/item names inside the JSON can't be mapped (no categories existed
in Part 1), so list-valued keys are ignored -- documented in DECISIONS.md.
"""
from decimal import Decimal, InvalidOperation

from django.db import migrations

MONEY_KEYS = ("daily_spend_cap", "weekly_spend_cap", "per_transaction_cap", "p2p_daily_cap", "low_balance_threshold")


def forwards(apps, schema_editor):
    School = apps.get_model("tenants", "School")
    Policy = apps.get_model("policies", "Policy")
    for school in School.objects.all():
        defaults = school.policy_defaults if isinstance(school.policy_defaults, dict) else {}
        values = {}
        for key in MONEY_KEYS:
            if defaults.get(key) not in (None, ""):
                try:
                    values[key] = Decimal(str(defaults[key]))
                except InvalidOperation:
                    pass
        if isinstance(defaults.get("p2p_enabled"), bool):
            values["p2p_enabled"] = defaults["p2p_enabled"]
        policy, _ = Policy.objects.get_or_create(school=school, student=None)
        for key, value in values.items():
            if getattr(policy, key) is None:
                setattr(policy, key, value)
        policy.save()


class Migration(migrations.Migration):
    dependencies = [("policies", "0001_initial"), ("tenants", "0001_initial")]

    operations = [migrations.RunPython(forwards, migrations.RunPython.noop)]

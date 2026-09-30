"""
manage.py run_recurring_topups [--now]

Runs the same service Celery Beat runs every 15 minutes
(payments.services.run_due_recurring_topups), immediately.
  default : execute every active recurring top-up whose next_run_at has passed
  --now   : treat EVERY active recurring top-up as due right now
Idempotent per run window: running it twice for the same window does nothing
the second time.
"""
from django.core.management.base import BaseCommand

from payments.models import RecurringTopUp
from payments.services import run_due_recurring_topups


class Command(BaseCommand):
    help = "Execute due recurring top-ups now (no need to wait for Celery Beat)."

    def add_arguments(self, parser):
        parser.add_argument("--now", action="store_true", help="Run every active schedule, not just the due ones.")

    def handle(self, *args, **opts):
        results = run_due_recurring_topups(force=opts["now"])
        if not results:
            self.stdout.write("No recurring top-ups were due." + ("" if opts["now"] else " (Use --now to force.)"))
        for r in results:
            rt = RecurringTopUp.objects.select_related("student").get(pk=r["recurring_topup"])
            self.stdout.write(
                f"#{rt.pk} {rt.student.name:<16} {rt.amount:>9} {rt.frequency:<8} -> {r['outcome']:<26} "
                f"next run {rt.next_run_at:%Y-%m-%d %H:%M} UTC, active={rt.active}, failures={rt.consecutive_failures}"
            )

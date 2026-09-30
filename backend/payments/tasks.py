from celery import shared_task

from . import services


@shared_task
def run_recurring_topups():
    return services.run_due_recurring_topups()


@shared_task
def expire_stale_deposits():
    return services.expire_stale_deposits()

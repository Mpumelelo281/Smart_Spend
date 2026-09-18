"""Rule 10's "never delays the response" half, now actually true: the
threshold check itself still runs the same cheap aggregate query as
before (see notifications.py), just on a Celery worker instead of inside
the request/response cycle.

TransactionSerializer.create() enqueues this via `.delay()`, but falls
back to calling it directly (synchronously) if enqueuing itself fails —
e.g. no broker reachable, such as local dev without Redis/a worker running.
See the try/except there: silently dropping the alert entirely would be
worse than occasionally not being fully async.
"""

import logging

from celery import shared_task

from .models import BudgetCategory
from .notifications import check_category_threshold

logger = logging.getLogger(__name__)


@shared_task(name="budgets.dispatch_threshold_check")
def dispatch_threshold_check(category_id) -> None:
    try:
        category = BudgetCategory.objects.get(pk=category_id)
    except BudgetCategory.DoesNotExist:
        # The category (or its budget) was deleted between the transaction
        # being logged and this task running — nothing left to alert on.
        logger.info("dispatch_threshold_check: category %s no longer exists.", category_id)
        return

    check_category_threshold(category)

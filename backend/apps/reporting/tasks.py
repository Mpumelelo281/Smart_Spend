"""Materialised views don't auto-update on write — something has to
periodically REFRESH them. Schedule this task via the django-celery-beat
admin (e.g. every 15 minutes); nothing calls it automatically otherwise.

Runs on the `default` connection, which owns the views, not `reporting` —
the restricted role is deliberately read-only (see db_router.py) and
cannot refresh them itself.
"""

import logging

from celery import shared_task
from django.db import connections

logger = logging.getLogger(__name__)

_REFRESH_STATEMENTS = [
    "REFRESH MATERIALIZED VIEW CONCURRENTLY reporting_category_spend_summary;",
    "REFRESH MATERIALIZED VIEW CONCURRENTLY reporting_budget_utilization_summary;",
]


@shared_task(name="reporting.refresh_reporting_views")
def refresh_reporting_views() -> None:
    with connections["default"].cursor() as cursor:
        for statement in _REFRESH_STATEMENTS:
            cursor.execute(statement)
    logger.info("Refreshed reporting materialised views.")

"""Rule 10: "Alert at 80% of a category allocation and again when
exceeded. Alerts state the category, the percentage and the rand amount
so they are actionable without opening the app."

The check itself (this module) stays a plain function — it's tasks.py's
`dispatch_threshold_check` Celery task that calls it off the
request/response cycle. Kept separate so the check can still be unit
tested (or called from the admin/a management command) without pulling in
Celery at all.
"""

from decimal import Decimal

from django.conf import settings
from django.db.models import Sum
from django.db.models.functions import Coalesce

from apps.notifications.models import Notification
from apps.notifications.push import send_web_push


def check_category_threshold(category) -> None:
    spent = category.transactions.aggregate(total=Coalesce(Sum("amount"), Decimal("0")))["total"]
    allocated = category.allocated_amount
    if allocated <= 0:
        return

    ratio = spent / allocated
    threshold = Decimal(settings.BUDGET_ALERT_THRESHOLD_PCT) / Decimal(100)

    if ratio >= 1:
        notif_type = Notification.NotifType.BUDGET_EXCEEDED
        message = (
            f"You've gone over your \"{category.name}\" budget: "
            f"R{spent} spent of R{allocated} allocated."
        )
    elif ratio >= threshold:
        notif_type = Notification.NotifType.BUDGET_THRESHOLD_80
        pct = int(ratio * 100)
        remaining = allocated - spent
        message = (
            f"You've used {pct}% of your \"{category.name}\" budget — "
            f"R{remaining} left of R{allocated}."
        )
    else:
        return

    # The DB constraint (one_threshold_notification_per_category_per_type)
    # is the real guarantee against duplicate alerts under concurrent
    # requests; this get_or_create just avoids relying on that constraint
    # raising an IntegrityError as the normal, expected path.
    notification, created = Notification.objects.get_or_create(
        related_category=category,
        notif_type=notif_type,
        defaults={
            "profile": category.budget.profile,
            "message": message,
            "channel": Notification.Channel.PUSH,
        },
    )
    if created:
        send_web_push.delay(notification.notification_id)

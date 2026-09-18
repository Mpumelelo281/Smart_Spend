"""A scheduled price-drop check, independent of live search's per-query
15-minute refresh (see live_search.py) — this looks at what's already in
PriceRecord (however it got there) and compares it against what each
student's cart last saw. Schedule via the django-celery-beat admin (e.g.
hourly); nothing calls this automatically otherwise.

One active alert per student per product (see Notification's
one_active_price_drop_notification_per_product constraint) — a student who
hasn't dismissed the last drop alert for a product doesn't get spammed by
every subsequent, smaller drop until they do.
"""

import logging

from celery import shared_task

from apps.notifications.models import Notification
from apps.notifications.push import send_web_push

from .models import CartItem, PriceRecord

logger = logging.getLogger(__name__)


@shared_task(name="catalog.check_price_drops")
def check_price_drops() -> None:
    for item in CartItem.objects.select_related("profile", "product").all():
        best = (
            PriceRecord.objects.filter(product=item.product, retailer__is_active=True)
            .order_by("price", "delivery_cost")
            .first()
        )
        if best is None:
            continue

        current_total = best.price + best.delivery_cost
        previous_total = item.price + item.delivery_cost
        if current_total >= previous_total:
            continue

        savings = previous_total - current_total
        message = (
            f'The price of "{item.product.name}" dropped by R{savings} '
            f"— now R{current_total} at {best.retailer.name}."
        )
        notification, created = Notification.objects.get_or_create(
            profile=item.profile,
            related_product=item.product,
            notif_type=Notification.NotifType.PRICE_DROP,
            is_read=False,
            defaults={"message": message, "channel": Notification.Channel.PUSH},
        )
        if created:
            send_web_push.delay(notification.notification_id)
        else:
            logger.debug(
                "Price drop on %s for %s already has an active alert; skipping.",
                item.product_id,
                item.profile_id,
            )

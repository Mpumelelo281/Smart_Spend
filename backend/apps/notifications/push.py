"""Web Push delivery for Notification.Channel.PUSH rows. Dispatched as a
Celery task from notifications.py (budgets' threshold checks) right after
a new Notification row is created — same "never block the request" reason
tasks.py's dispatch_threshold_check exists.

Sending is best-effort: a browser can revoke a push subscription at any
time without telling the server, so a 404/410 from the push service means
"this subscription is dead", not "retry me" — see the WebPushException
handling below. Every other failure is logged and otherwise ignored; the
in-app Notification row (and email, where configured) already carries the
alert regardless of whether push delivery succeeds.
"""

import json
import logging

from celery import shared_task
from django.conf import settings
from pywebpush import WebPushException, webpush

from .models import Notification, PushSubscription

logger = logging.getLogger(__name__)


@shared_task(name="notifications.send_web_push")
def send_web_push(notification_id) -> None:
    if not (settings.VAPID_PUBLIC_KEY and settings.VAPID_PRIVATE_KEY):
        logger.info("send_web_push: VAPID keys are not configured — skipping.")
        return

    try:
        notification = Notification.objects.select_related("profile").get(pk=notification_id)
    except Notification.DoesNotExist:
        return

    subscriptions = PushSubscription.objects.filter(profile=notification.profile)
    if not subscriptions:
        return

    payload = json.dumps(
        {
            "title": "SmartSpend",
            "body": notification.message,
            "notification_id": str(notification.notification_id),
        }
    )

    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {"p256dh": subscription.p256dh, "auth": subscription.auth},
                },
                data=payload,
                vapid_private_key=settings.VAPID_PRIVATE_KEY,
                vapid_claims={"sub": f"mailto:{settings.VAPID_ADMIN_EMAIL}"},
            )
        except WebPushException as exc:
            status_code = exc.response.status_code if exc.response is not None else None
            if status_code in (404, 410):
                # The browser/push service has permanently revoked this
                # endpoint — stop trying it rather than fail forever.
                subscription.delete()
            else:
                logger.warning("Web push failed for subscription %s: %s", subscription.pk, exc)

"""Entity: Notification (1 of the 11).

Rule 10 ("alert at 80% of a category allocation and again when exceeded")
is wired up via apps/budgets/notifications.py::check_category_threshold,
dispatched from a Celery task (apps/budgets/tasks.py) so logging a
transaction never waits on the alert check — Rule 10's "never delays the
response".
"""

import uuid

from django.db import models

from apps.accounts.models import StudentProfile


class Notification(models.Model):
    class Channel(models.TextChoices):
        EMAIL = "EMAIL", "Email"
        PUSH = "PUSH", "Web Push"

    class NotifType(models.TextChoices):
        BUDGET_THRESHOLD_80 = "BUDGET_THRESHOLD_80", "80% of category allocation reached"
        BUDGET_EXCEEDED = "BUDGET_EXCEEDED", "Category allocation exceeded"
        PRICE_DROP = "PRICE_DROP", "Price drop on a watched product"
        SYSTEM = "SYSTEM", "System message"

    notification_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="notifications")
    notif_type = models.CharField(max_length=30, choices=NotifType.choices)
    message = models.TextField()
    channel = models.CharField(max_length=10, choices=Channel.choices)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Additive, not one of the 11 ERD fields: lets a threshold check ask
    # "have we already alerted on this category crossing this threshold"
    # in one query instead of parsing `message` text. Null for
    # notification types that aren't about a specific category (e.g. a
    # future PRICE_DROP or SYSTEM message).
    related_category = models.ForeignKey(
        "budgets.BudgetCategory",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    # PRICE_DROP alerts (apps/catalog/tasks.py::check_price_drops) — null
    # for every other notif_type, same reasoning as related_category above.
    related_product = models.ForeignKey(
        "catalog.Product",
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name="notifications",
    )

    class Meta:
        db_table = "notification"
        indexes = [models.Index(fields=["is_read"]), models.Index(fields=["created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["related_category", "notif_type"],
                name="one_threshold_notification_per_category_per_type",
                condition=models.Q(related_category__isnull=False),
            ),
            # One *active* (unread) price-drop alert per student per
            # product — once dismissed (is_read=True), the row drops out
            # of this partial index and a later drop can alert again.
            models.UniqueConstraint(
                fields=["profile", "related_product", "notif_type"],
                name="one_active_price_drop_notification_per_product",
                condition=models.Q(related_product__isnull=False, is_read=False),
            ),
        ]

    def __str__(self):
        return f"{self.notif_type} -> {self.profile_id}"


class PushSubscription(models.Model):
    """A browser's Web Push subscription (from the PushManager API),
    registered once per device/browser the student opts in on. Channel.PUSH
    notifications are delivered to every row here for that student — see
    apps/notifications/push.py::send_web_push.
    """

    subscription_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    profile = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name="push_subscriptions")
    # Push service endpoints (e.g. Chrome's FCM, Firefox's autopush) run
    # well past Django's default URLField length.
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "push_subscription"
        constraints = [
            models.UniqueConstraint(
                fields=["profile", "endpoint"], name="one_subscription_per_profile_per_endpoint"
            )
        ]

    def __str__(self):
        return f"push subscription for {self.profile_id}"

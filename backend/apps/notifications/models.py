"""Entity: Notification (1 of the 11).

Rule 10 ("alert at 80% of a category allocation and again when exceeded")
is now wired up — see apps/budgets/notifications.py, called synchronously
from TransactionSerializer.create() rather than a Celery task, since this
dev environment doesn't run a Celery worker; the check itself is cheap
(one aggregate query), so this is a reasonable interim home for it.
Moving the dispatch itself off the request/response cycle (Rule 10's
"never delays the response") is the natural next step once Celery is
actually running.
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

    class Meta:
        db_table = "notification"
        indexes = [models.Index(fields=["is_read"]), models.Index(fields=["created_at"])]
        constraints = [
            models.UniqueConstraint(
                fields=["related_category", "notif_type"],
                name="one_threshold_notification_per_category_per_type",
                condition=models.Q(related_category__isnull=False),
            )
        ]

    def __str__(self):
        return f"{self.notif_type} -> {self.profile_id}"

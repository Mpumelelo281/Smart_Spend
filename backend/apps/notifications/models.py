"""Entity: Notification (1 of the 11).

Rule 10 ("threshold notifications ... dispatch as a background job so it
never delays the response") is implemented as a Celery task in Sprint 3,
which will write rows here; this app is model-only for Sprint 1.
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

    class Meta:
        db_table = "notification"
        indexes = [models.Index(fields=["is_read"]), models.Index(fields=["created_at"])]

    def __str__(self):
        return f"{self.notif_type} -> {self.profile_id}"

from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["notification_id", "notif_type", "message", "channel", "is_read", "created_at"]
        read_only_fields = fields

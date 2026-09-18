from rest_framework import serializers

from .models import Notification, PushSubscription


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ["notification_id", "notif_type", "message", "channel", "is_read", "created_at"]
        read_only_fields = fields


class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ["subscription_id", "endpoint", "p256dh", "auth"]
        read_only_fields = ["subscription_id"]

    def create(self, validated_data):
        # A student re-subscribing the same browser (e.g. after clearing
        # site data) sends the same endpoint with new keys — replace
        # rather than error, so the frontend never has to check first.
        subscription, _ = PushSubscription.objects.update_or_create(
            profile=self.context["profile"],
            endpoint=validated_data["endpoint"],
            defaults={"p256dh": validated_data["p256dh"], "auth": validated_data["auth"]},
        )
        return subscription

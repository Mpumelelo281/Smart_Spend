from rest_framework import serializers


class AssistantMessageSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=500, trim_whitespace=True)

    def validate_message(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Message is required.")
        return value

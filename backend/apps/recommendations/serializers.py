from rest_framework import serializers

from .engine import best_current_offer
from .models import Preference, Recommendation


class PreferenceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preference
        fields = ["preference_id", "pref_type", "pref_value", "radius_km"]

    def validate_pref_type(self, value):
        if value not in ("category", "location"):
            raise serializers.ValidationError('pref_type must be "category" or "location".')
        return value

    def create(self, validated_data):
        validated_data["profile"] = self.context["profile"]
        return super().create(validated_data)


class RecommendationSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source="product.name")
    category = serializers.CharField(source="product.category")
    offer = serializers.SerializerMethodField()

    class Meta:
        model = Recommendation
        fields = [
            "recommendation_id",
            "product_id",
            "product_name",
            "category",
            "rank_position",
            "was_accepted",
            "issued_at",
            "offer",
        ]
        read_only_fields = fields

    def get_offer(self, obj):
        record = best_current_offer(obj.product)
        if record is None:
            return None
        return {
            "retailer_id": record.retailer_id,
            "retailer_name": record.retailer.name,
            "price": record.price,
            "delivery_cost": record.delivery_cost,
            "total_landed_cost": record.total_landed_cost,
        }


class RecommendationFeedbackSerializer(serializers.Serializer):
    was_accepted = serializers.BooleanField()

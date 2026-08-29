from rest_framework import serializers


class PriceSearchResultSerializer(serializers.Serializer):
    """Shapes one PriceRecord (joined with its Product/Retailer) into a
    search result row. Not a ModelSerializer: the row mixes fields from
    three tables plus a computed distance, so there's no single model to
    hang it off.
    """

    product_id = serializers.UUIDField()
    name = serializers.CharField()
    category = serializers.CharField()
    color = serializers.CharField(allow_null=True)
    size = serializers.CharField(allow_null=True)

    retailer_id = serializers.UUIDField()
    retailer_name = serializers.CharField()
    store_address = serializers.CharField(allow_blank=True)

    price = serializers.DecimalField(max_digits=8, decimal_places=2)
    delivery_cost = serializers.DecimalField(max_digits=8, decimal_places=2)
    # Rule 3: total landed cost, not item price, is what the interface
    # leads with and the primary sort key.
    total_landed_cost = serializers.DecimalField(max_digits=8, decimal_places=2)

    distance_km = serializers.DecimalField(max_digits=6, decimal_places=1, allow_null=True)
    retrieved_at = serializers.DateTimeField()

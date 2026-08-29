"""Product price search.

This queries locally-stored PriceRecord rows (seeded via `manage.py
seed_catalog` for now — see models.py docstring). The retailer-adapter
layer that would keep these rows fresh from live retailer sites, behind
circuit breakers and the 15-minute Redis cache, is still Sprint 2
architecture work; this view is written against the same PriceRecord table
that layer will populate, so nothing here changes when that lands.
"""

from django.db.models import DecimalField, ExpressionWrapper, F
from rest_framework import permissions
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import StudentProfile

from .geo import distance_from_campus_km
from .models import PriceRecord
from .serializers import PriceSearchResultSerializer

SORT_OPTIONS = {
    "landed_cost_asc": "landed_cost",
    "landed_cost_desc": "-landed_cost",
}


class ProductSearchView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        color = request.query_params.get("color", "").strip()
        size = request.query_params.get("size", "").strip()
        # Rule 3: landed cost ascending (cheapest first) is the default —
        # "highest to lowest" is offered as an explicit opt-in, not the
        # default, so a student comparing prices sees the best deal first
        # unless they deliberately ask to sort the other way.
        sort = request.query_params.get("sort", "landed_cost_asc")
        if sort not in SORT_OPTIONS:
            sort = "landed_cost_asc"

        records = (
            PriceRecord.objects.select_related("product", "retailer")
            .filter(retailer__is_active=True)
            .annotate(
                # Named `landed_cost`, not `total_landed_cost` — that name
                # is PriceRecord.total_landed_cost, a read-only @property.
                # Django's ORM tries to setattr() every annotated field
                # onto the resulting instances, which raises AttributeError
                # against a property with no setter.
                landed_cost=ExpressionWrapper(
                    F("price") + F("delivery_cost"), output_field=DecimalField(max_digits=8, decimal_places=2)
                )
            )
        )

        if query:
            records = records.filter(product__name__icontains=query)
        if color:
            records = records.filter(product__attributes__color__iexact=color)
        if size:
            records = records.filter(product__attributes__size__iexact=size)

        records = records.order_by(SORT_OPTIONS[sort])[:50]

        profile = StudentProfile.objects.filter(user=request.user).first()
        campus = profile.campus if profile else ""

        results = []
        for record in records:
            attrs = record.product.attributes or {}
            results.append(
                {
                    "product_id": record.product_id,
                    "name": record.product.name,
                    "category": record.product.category,
                    "color": attrs.get("color"),
                    "size": attrs.get("size"),
                    "retailer_id": record.retailer_id,
                    "retailer_name": record.retailer.name,
                    "store_address": record.retailer.store_address,
                    "price": record.price,
                    "delivery_cost": record.delivery_cost,
                    "total_landed_cost": record.landed_cost,
                    "distance_km": distance_from_campus_km(campus, record.retailer),
                    "retrieved_at": record.retrieved_at,
                }
            )

        serializer = PriceSearchResultSerializer(results, many=True)
        return Response({"count": len(results), "results": serializer.data})

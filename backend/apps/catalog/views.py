"""Product price search.

On a query, `live_search.ensure_live_data` first gives the SerpApi Google
Shopping adapter a chance to refresh PriceRecord (subject to Rule 4's
15-minute per-query cache and Rule 6's circuit breaker — see
adapters/serpapi_google_shopping.py). Either way, what actually gets
served below is always read straight from PriceRecord — a live-fetch
failure degrades to "whatever was already there", never a broken response.
"""

from decimal import Decimal

from django.db.models import DecimalField, ExpressionWrapper, F, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.models import StudentProfile
from apps.accounts.permissions import IsStudent

from .geo import resolve_distance_km
from .live_search import ensure_live_data
from .models import CartItem, PriceRecord, Product
from .serializers import (
    CartAddSerializer,
    CartItemQuantitySerializer,
    CartItemSerializer,
    PriceSearchResultSerializer,
)

SUGGESTION_LIMIT = 8

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

        ensure_live_data(query)

        # Live refreshes create a *new* PriceRecord snapshot rather than
        # overwriting one (see live_search.py) — so the same product at
        # the same retailer can have several historical rows. Keep only
        # the newest one per (product, retailer) before anything else, or
        # results would show visibly duplicated listings the longer the
        # app runs.
        latest_per_product_retailer = (
            PriceRecord.objects.filter(product=OuterRef("product"), retailer=OuterRef("retailer"))
            .order_by("-retrieved_at")
            .values("price_id")[:1]
        )

        records = (
            PriceRecord.objects.select_related("product", "retailer")
            .filter(retailer__is_active=True, price_id=Subquery(latest_per_product_retailer))
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
        # Real browser geolocation (opt-in — see the frontend's "Use my
        # location" control) takes priority over the campus lookup when
        # both are sent; see geo.resolve_distance_km.
        lat = request.query_params.get("lat")
        lon = request.query_params.get("lon")
        radius_km = request.query_params.get("radius_km")
        try:
            radius_km = float(radius_km) if radius_km else None
        except ValueError:
            radius_km = None

        results = []
        for record in records:
            distance_km = resolve_distance_km(campus, lat, lon, record.retailer)
            # A radius filter only makes sense against a real distance —
            # online-only listings (distance_km is None) are never
            # excluded by it, since "25km away" doesn't apply to them.
            if radius_km is not None and distance_km is not None and float(distance_km) > radius_km:
                continue

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
                    "distance_km": distance_km,
                    "retrieved_at": record.retrieved_at,
                }
            )

        serializer = PriceSearchResultSerializer(results, many=True)
        return Response({"count": len(results), "results": serializer.data})


class ProductSuggestionsView(APIView):
    """Lightweight name-only lookup for the search box's autocomplete
    dropdown — deliberately not the full search (no prices/joins/distance)
    so it stays fast enough to call on every keystroke.
    """

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            return Response({"results": []})

        names = (
            Product.objects.filter(name__icontains=query)
            .values_list("name", "category")
            .distinct()[:SUGGESTION_LIMIT]
        )
        return Response({"results": [{"name": name, "category": category} for name, category in names]})


def _latest_price_record(product_id, retailer_id):
    return (
        PriceRecord.objects.filter(product_id=product_id, retailer_id=retailer_id)
        .order_by("-retrieved_at")
        .first()
    )


class CartListCreateView(generics.ListCreateAPIView):
    """A student's "planning to buy" list. price/delivery_cost are always
    snapshotted here from the latest PriceRecord server-side (never taken
    from the request body) — same "server is authoritative" rule as
    Rule 1's budget allocation, applied to price this time.
    """

    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = CartItemSerializer

    def get_queryset(self):
        return (
            CartItem.objects.select_related("product", "retailer")
            .filter(profile__user=self.request.user)
            .order_by("-added_at")
        )

    def list(self, request, *args, **kwargs):
        # Bypasses the project's default pagination deliberately — a
        # student's cart is never large enough to need it, and cart_total
        # has to be computed from real Decimal objects, not the
        # already-stringified values in a serialized/paginated response.
        items = list(self.get_queryset())
        cart_total = sum((item.line_total for item in items), Decimal("0"))
        serializer = self.get_serializer(items, many=True)
        return Response({"results": serializer.data, "cart_total": cart_total})

    def create(self, request, *args, **kwargs):
        payload = CartAddSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        product_id = payload.validated_data["product_id"]
        retailer_id = payload.validated_data["retailer_id"]
        quantity = payload.validated_data["quantity"]

        price_record = _latest_price_record(product_id, retailer_id)
        if price_record is None:
            return Response(
                {"detail": "No current price found for that item at that store."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        profile = get_object_or_404(StudentProfile, user=request.user)
        item, created = CartItem.objects.get_or_create(
            profile=profile,
            product_id=product_id,
            retailer_id=retailer_id,
            defaults={
                "price": price_record.price,
                "delivery_cost": price_record.delivery_cost,
                "quantity": quantity,
            },
        )
        if not created:
            item.quantity += quantity
            # Refresh the price snapshot to the current one on every add,
            # so a cart line doesn't quietly go stale if prices moved.
            item.price = price_record.price
            item.delivery_cost = price_record.delivery_cost
            item.save(update_fields=["quantity", "price", "delivery_cost"])

        return Response(CartItemSerializer(item).data, status=status.HTTP_201_CREATED)


class CartItemDetailView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated, IsStudent]
    serializer_class = CartItemQuantitySerializer

    def get_object(self):
        return get_object_or_404(
            CartItem, cart_item_id=self.kwargs["cart_item_id"], profile__user=self.request.user
        )

    def patch(self, request, cart_item_id):
        item = self.get_object()
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity"])
        return Response(CartItemSerializer(item).data)

    def delete(self, request, cart_item_id):
        self.get_object().delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

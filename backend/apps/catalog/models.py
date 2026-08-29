"""Entities: Product, Retailer, PriceRecord (3 of the 11).

Search (views.py::ProductSearchView) now reads this data — filtering by
name/color/size, sorting by total landed cost, and computing distance from
the student's campus to each retailer's store. The retailer adapters,
circuit breakers and 15-minute Redis cache (Rules 4 and 6) that would keep
PriceRecord populated from *live* retailer sites are still Sprint 2 work;
for now these rows come from the `seed_catalog` management command (see
apps/catalog/management/commands/seed_catalog.py), not a live fetch.
"""

import uuid

from django.db import models


class Retailer(models.Model):
    class IntegrationType(models.TextChoices):
        API = "API", "Official API"
        SCRAPER = "SCRAPER", "Scheduled scraper (where permitted by terms of use)"

    retailer_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    integration_type = models.CharField(max_length=10, choices=IntegrationType.choices)
    base_url = models.URLField()
    # Rule 6: a source failing its health check is stored inactive, not
    # discarded, so it can be brought back once it recovers.
    is_active = models.BooleanField(default=True)

    # Physical store location, for "how far is it" in search results.
    # Nullable: an online-only retailer has prices but no store to travel
    # to, and distance is simply omitted for it in the API response rather
    # than faked.
    store_address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "retailer"

    def __str__(self):
        return self.name


class Product(models.Model):
    product_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=80)
    # Variable retailer-specific attributes (pack size, brand, unit, ...).
    # PostgreSQL JSONB, per the mandated stack.
    attributes = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "product"
        indexes = [models.Index(fields=["category"])]

    def __str__(self):
        return self.name


class PriceRecord(models.Model):
    """The fact of interest is "price of this product at this retailer at
    this moment" — see the schema rationale in the build brief. Without the
    `retrieved_at` timestamp, cross-retailer comparison and price-drop
    alerts are both impossible.
    """

    price_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="price_records")
    retailer = models.ForeignKey(Retailer, on_delete=models.CASCADE, related_name="price_records")
    price = models.DecimalField(max_digits=8, decimal_places=2)
    delivery_cost = models.DecimalField(max_digits=8, decimal_places=2, default=0)
    retrieved_at = models.DateTimeField()

    class Meta:
        db_table = "price_record"
        constraints = [
            models.UniqueConstraint(
                fields=["product", "retailer", "retrieved_at"], name="unique_price_snapshot"
            ),
            models.CheckConstraint(check=models.Q(price__gte=0), name="price_non_negative"),
            models.CheckConstraint(check=models.Q(delivery_cost__gte=0), name="delivery_cost_non_negative"),
        ]
        indexes = [
            models.Index(fields=["price"]),
            models.Index(fields=["retrieved_at"]),
        ]

    def __str__(self):
        return f"{self.product_id}@{self.retailer_id}: R{self.price} ({self.retrieved_at:%Y-%m-%d %H:%M})"

    @property
    def total_landed_cost(self):
        # Rule 3: total landed cost, not item price, is the figure the
        # interface leads with and the primary sort key in Sprint 2 search.
        return self.price + self.delivery_cost

"""Populates a small, realistic demo catalogue so the search feature has
something to search over. This stands in for the retailer-adapter layer
(Sprint 2) that would keep PriceRecord fresh from live retailer sites —
see the docstring at the top of apps/catalog/models.py. Safe to re-run:
everything is get_or_create / update_or_create.

    python manage.py seed_catalog
"""

from datetime import timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.catalog.models import PriceRecord, Product, Retailer

RETAILERS = [
    # name, integration_type, base_url, address, lat, lon
    ("Boxer Musgrave", "SCRAPER", "https://www.boxer.co.za",
     "45 Anton Lembede St, Durban", -29.8578, 31.0206),
    ("Shoprite Berea Centre", "SCRAPER", "https://www.shoprite.co.za",
     "Berea Centre, Ridge Rd, Durban", -29.8390, 30.9985),
    ("Checkers Overport", "SCRAPER", "https://www.checkers.co.za",
     "Overport City, Durban", -29.8324, 30.9989),
    ("PEP Warwick Junction", "SCRAPER", "https://www.pepstores.com",
     "Warwick Ave, Durban", -29.8560, 31.0064),
    # Online-only: no physical store, so distance is legitimately unknown.
    ("Takealot", "API", "https://www.takealot.com", "", None, None),
]

PRODUCTS = [
    # name, category, attributes, [(retailer_name, price, delivery_cost), ...]
    (
        "Colgate Total Toothpaste 100ml",
        "Toiletries",
        {"size": "100ml", "brand": "Colgate"},
        [
            ("Boxer Musgrave", "24.99", "0.00"),
            ("Shoprite Berea Centre", "26.50", "0.00"),
            ("Takealot", "29.00", "45.00"),
        ],
    ),
    (
        "Dove Beauty Bar Soap",
        "Toiletries",
        {"size": "100g", "color": "White", "brand": "Dove"},
        [("Boxer Musgrave", "14.99", "0.00"), ("Checkers Overport", "15.99", "0.00")],
    ),
    (
        "Nivea Men Roll-On Deodorant",
        "Toiletries",
        {"size": "50ml", "color": "Black", "brand": "Nivea"},
        [
            ("Shoprite Berea Centre", "32.99", "0.00"),
            ("Checkers Overport", "34.99", "0.00"),
            ("Takealot", "31.50", "45.00"),
        ],
    ),
    (
        "Vaseline Intensive Care Lotion",
        "Toiletries",
        {"size": "400ml", "brand": "Vaseline"},
        [("Boxer Musgrave", "49.99", "0.00"), ("Takealot", "52.00", "45.00")],
    ),
    (
        "White Star Maize Meal 5kg",
        "Groceries",
        {"size": "5kg", "brand": "White Star"},
        [
            ("Boxer Musgrave", "79.99", "0.00"),
            ("Shoprite Berea Centre", "82.99", "0.00"),
            ("PEP Warwick Junction", "84.99", "0.00"),
        ],
    ),
    (
        "Clover Fresh Milk 2L",
        "Groceries",
        {"size": "2L", "brand": "Clover"},
        [("Shoprite Berea Centre", "34.99", "0.00"), ("Checkers Overport", "36.50", "0.00")],
    ),
    (
        "Sunlight Dishwashing Liquid",
        "Groceries",
        {"size": "750ml", "brand": "Sunlight"},
        [("Boxer Musgrave", "27.99", "0.00"), ("Checkers Overport", "29.99", "0.00")],
    ),
    (
        "Bic Ballpoint Pens (Pack of 10)",
        "Study Materials",
        {"color": "Blue", "size": "Pack of 10", "brand": "Bic"},
        [("PEP Warwick Junction", "39.99", "0.00"), ("Takealot", "42.00", "45.00")],
    ),
    (
        "A4 Ruled Notebook 72 Pages",
        "Study Materials",
        {"color": "Black", "size": "A4", "brand": "Generic"},
        [("PEP Warwick Junction", "18.99", "0.00"), ("Boxer Musgrave", "19.99", "0.00")],
    ),
    (
        "Reflex Crew Neck T-Shirt",
        "Clothing",
        {"color": "Navy", "size": "M", "brand": "Reflex"},
        [("PEP Warwick Junction", "89.99", "0.00"), ("Takealot", "99.00", "45.00")],
    ),
    (
        "Reflex Crew Neck T-Shirt",
        "Clothing",
        {"color": "White", "size": "M", "brand": "Reflex"},
        [("PEP Warwick Junction", "89.99", "0.00")],
    ),
]


class Command(BaseCommand):
    help = "Seed demo retailers, products and prices for the search feature."

    def handle(self, *args, **options):
        retailers = {}
        for name, integration_type, base_url, address, lat, lon in RETAILERS:
            retailer, _ = Retailer.objects.update_or_create(
                name=name,
                defaults={
                    "integration_type": integration_type,
                    "base_url": base_url,
                    "store_address": address,
                    "latitude": Decimal(str(lat)) if lat is not None else None,
                    "longitude": Decimal(str(lon)) if lon is not None else None,
                    "is_active": True,
                },
            )
            retailers[name] = retailer

        now = timezone.now()
        created = 0
        for name, category, attributes, prices in PRODUCTS:
            product, _ = Product.objects.get_or_create(
                name=name,
                category=category,
                defaults={"attributes": attributes},
            )
            # Keep attributes in sync if the product already existed with
            # a stale value (still idempotent — no duplicate products).
            if product.attributes != attributes:
                product.attributes = attributes
                product.save(update_fields=["attributes"])

            for retailer_name, price, delivery_cost in prices:
                _, was_created = PriceRecord.objects.update_or_create(
                    product=product,
                    retailer=retailers[retailer_name],
                    retrieved_at=now.replace(minute=0, second=0, microsecond=0) - timedelta(hours=1),
                    defaults={"price": Decimal(price), "delivery_cost": Decimal(delivery_cost)},
                )
                created += was_created

        self.stdout.write(
            self.style.SUCCESS(
                f"Seeded {len(retailers)} retailers, {len(PRODUCTS)} products, {created} new price records."
            )
        )

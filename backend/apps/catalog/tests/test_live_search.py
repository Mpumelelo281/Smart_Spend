from datetime import timedelta
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog import live_search
from apps.catalog.adapters.base import AdapterUnavailable, NormalizedListing, RetailerAdapter
from apps.catalog.models import PriceRecord, Product, Retailer

pytestmark = pytest.mark.django_db


class _FakeAdapter(RetailerAdapter):
    name = "fake"

    def __init__(self, listings=None, error=None):
        self._listings = listings or []
        self._error = error

    def is_configured(self):
        return True

    def search(self, query):
        if self._error:
            raise self._error
        return self._listings


def test_ensure_live_data_persists_normalized_listings(monkeypatch):
    listing = NormalizedListing(
        product_name="Live Toothpaste",
        retailer_name="Live Retailer",
        price=19.99,
        delivery_cost=5.0,
    )
    monkeypatch.setattr(live_search, "ACTIVE_ADAPTERS", [lambda: _FakeAdapter([listing])])

    live_search.ensure_live_data("toothpaste")

    retailer = Retailer.objects.get(name="Live Retailer")
    product = Product.objects.get(name="Live Toothpaste")
    record = PriceRecord.objects.get(product=product, retailer=retailer)
    assert record.price == Decimal("19.99")
    assert record.delivery_cost == Decimal("5.0")
    assert retailer.integration_type == Retailer.IntegrationType.API


def test_ensure_live_data_skips_unconfigured_adapters(monkeypatch):
    class Unconfigured(RetailerAdapter):
        def is_configured(self):
            return False

        def search(self, query):
            raise AssertionError("should never be called when unconfigured")

    monkeypatch.setattr(live_search, "ACTIVE_ADAPTERS", [Unconfigured])
    live_search.ensure_live_data("anything")  # must not raise
    assert Product.objects.count() == 0


def test_ensure_live_data_survives_adapter_failure(monkeypatch):
    monkeypatch.setattr(
        live_search, "ACTIVE_ADAPTERS", [lambda: _FakeAdapter(error=AdapterUnavailable("down"))]
    )
    live_search.ensure_live_data("anything")  # must not raise
    assert PriceRecord.objects.count() == 0


def test_ensure_live_data_respects_the_15_minute_cache(monkeypatch):
    calls = []

    class CountingAdapter(_FakeAdapter):
        def search(self, query):
            calls.append(query)
            return []

    monkeypatch.setattr(live_search, "ACTIVE_ADAPTERS", [CountingAdapter])

    live_search.ensure_live_data("milk")
    live_search.ensure_live_data("milk")  # second call within the window: no new fetch

    assert len(calls) == 1


def test_search_returns_only_the_newest_snapshot_per_product_and_retailer(authenticated_client):
    retailer = Retailer.objects.create(
        name="History Store", integration_type=Retailer.IntegrationType.SCRAPER, base_url="https://x.example"
    )
    product = Product.objects.create(name="Snapshot Item", category="Test")
    old = timezone.now() - timedelta(hours=2)
    new = timezone.now()

    PriceRecord.objects.create(product=product, retailer=retailer, price=Decimal("100.00"), retrieved_at=old)
    PriceRecord.objects.create(product=product, retailer=retailer, price=Decimal("80.00"), retrieved_at=new)

    response = authenticated_client.get("/api/v1/catalog/search/", {"q": "Snapshot"})

    assert response.data["count"] == 1
    assert Decimal(response.data["results"][0]["price"]) == Decimal("80.00")

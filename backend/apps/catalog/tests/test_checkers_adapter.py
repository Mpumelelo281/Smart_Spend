import pybreaker
import pytest
import requests

from apps.catalog.adapters.base import AdapterUnavailable
from apps.catalog.adapters.checkers import CheckersAdapter

pytestmark = pytest.mark.django_db


def test_not_configured_without_a_base_url(settings):
    settings.CHECKERS_API_BASE_URL = ""
    assert CheckersAdapter().is_configured() is False


def test_configured_with_a_base_url(settings):
    settings.CHECKERS_API_BASE_URL = "https://example.test/checkers/search"
    assert CheckersAdapter().is_configured() is True


def test_search_without_a_base_url_raises_adapter_unavailable(settings):
    settings.CHECKERS_API_BASE_URL = ""
    with pytest.raises(AdapterUnavailable):
        CheckersAdapter().search("rice")


def test_normalize_skips_rows_missing_price():
    assert CheckersAdapter._normalize({"name": "Rice 2kg"}) is None


def test_normalize_extracts_core_fields():
    raw = {"name": "Rice 2kg", "price": 45.99, "category": "Groceries", "delivery_cost": 20}
    listing = CheckersAdapter._normalize(raw)

    assert listing.product_name == "Rice 2kg"
    assert listing.retailer_name == "Checkers"
    assert listing.price == 45.99
    assert listing.delivery_cost == 20.0
    assert listing.category == "Groceries"
    assert listing.retailer_base_url == "https://www.checkers.co.za"


def test_search_wraps_request_exceptions_as_adapter_unavailable(settings, monkeypatch):
    settings.CHECKERS_API_BASE_URL = "https://example.test/checkers/search"
    adapter = CheckersAdapter()

    def boom(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr("apps.catalog.adapters.checkers.requests.get", boom)

    with pytest.raises(AdapterUnavailable):
        adapter.search("rice")


def test_open_circuit_breaker_raises_adapter_unavailable(settings, monkeypatch):
    settings.CHECKERS_API_BASE_URL = "https://example.test/checkers/search"
    adapter = CheckersAdapter()

    def already_open(*args, **kwargs):
        raise pybreaker.CircuitBreakerError("circuit is open")

    monkeypatch.setattr(adapter, "_call_api", already_open)

    with pytest.raises(AdapterUnavailable):
        adapter.search("rice")


def test_search_returns_normalized_listings(settings, monkeypatch):
    settings.CHECKERS_API_BASE_URL = "https://example.test/checkers/search"
    adapter = CheckersAdapter()

    monkeypatch.setattr(
        adapter,
        "_call_api",
        lambda query: {"results": [{"name": "Rice 2kg", "price": 45.99, "category": "Groceries"}]},
    )

    listings = adapter.search("rice")
    assert len(listings) == 1
    assert listings[0].product_name == "Rice 2kg"

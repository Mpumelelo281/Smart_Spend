import pybreaker
import pytest
import requests

from apps.catalog.adapters.base import AdapterUnavailable
from apps.catalog.adapters.shoprite import ShopriteAdapter

pytestmark = pytest.mark.django_db


def test_not_configured_without_a_base_url(settings):
    settings.SHOPRITE_API_BASE_URL = ""
    assert ShopriteAdapter().is_configured() is False


def test_configured_with_a_base_url(settings):
    settings.SHOPRITE_API_BASE_URL = "https://example.test/shoprite/search"
    assert ShopriteAdapter().is_configured() is True


def test_search_without_a_base_url_raises_adapter_unavailable(settings):
    settings.SHOPRITE_API_BASE_URL = ""
    with pytest.raises(AdapterUnavailable):
        ShopriteAdapter().search("bread")


def test_normalize_skips_rows_missing_price():
    assert ShopriteAdapter._normalize({"name": "Brown Bread"}) is None


def test_normalize_extracts_core_fields():
    raw = {"name": "Brown Bread", "price": 18.99, "category": "Groceries"}
    listing = ShopriteAdapter._normalize(raw)

    assert listing.product_name == "Brown Bread"
    assert listing.retailer_name == "Shoprite"
    assert listing.price == 18.99
    assert listing.delivery_cost == 0.0
    assert listing.retailer_base_url == "https://www.shoprite.co.za"


def test_search_wraps_request_exceptions_as_adapter_unavailable(settings, monkeypatch):
    settings.SHOPRITE_API_BASE_URL = "https://example.test/shoprite/search"
    adapter = ShopriteAdapter()

    def boom(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr("apps.catalog.adapters.shoprite.requests.get", boom)

    with pytest.raises(AdapterUnavailable):
        adapter.search("bread")


def test_open_circuit_breaker_raises_adapter_unavailable(settings, monkeypatch):
    settings.SHOPRITE_API_BASE_URL = "https://example.test/shoprite/search"
    adapter = ShopriteAdapter()

    def already_open(*args, **kwargs):
        raise pybreaker.CircuitBreakerError("circuit is open")

    monkeypatch.setattr(adapter, "_call_api", already_open)

    with pytest.raises(AdapterUnavailable):
        adapter.search("bread")

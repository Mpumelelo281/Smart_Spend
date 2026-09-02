import pybreaker
import pytest
import requests

from apps.catalog.adapters.base import AdapterUnavailable
from apps.catalog.adapters.serpapi_google_shopping import SerpApiGoogleShoppingAdapter

pytestmark = pytest.mark.django_db


def test_not_configured_without_a_key(settings):
    settings.SERPAPI_KEY = ""
    assert SerpApiGoogleShoppingAdapter().is_configured() is False


def test_configured_with_a_key(settings):
    settings.SERPAPI_KEY = "test-key"
    assert SerpApiGoogleShoppingAdapter().is_configured() is True


def test_search_without_a_key_raises_adapter_unavailable(settings):
    settings.SERPAPI_KEY = ""
    with pytest.raises(AdapterUnavailable):
        SerpApiGoogleShoppingAdapter().search("toothpaste")


def test_normalize_skips_rows_missing_price():
    raw = {"title": "Some Item", "source": "Some Store"}  # no extracted_price
    assert SerpApiGoogleShoppingAdapter._normalize(raw) is None


def test_normalize_extracts_core_fields():
    raw = {
        "title": "Colgate Toothpaste",
        "source": "Takealot",
        "extracted_price": 24.99,
        "product_link": "https://www.takealot.com/some-product/PLID123",
    }
    listing = SerpApiGoogleShoppingAdapter._normalize(raw)

    assert listing.product_name == "Colgate Toothpaste"
    assert listing.retailer_name == "Takealot"
    assert listing.price == 24.99
    assert listing.delivery_cost == 0.0
    assert listing.retailer_base_url == "https://www.takealot.com"
    # Never fabricated — SerpApi doesn't reliably give these.
    assert listing.color is None
    assert listing.size is None
    assert listing.store_address is None


def test_search_wraps_request_exceptions_as_adapter_unavailable(settings, monkeypatch):
    settings.SERPAPI_KEY = "test-key"
    adapter = SerpApiGoogleShoppingAdapter()

    def boom(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr("apps.catalog.adapters.serpapi_google_shopping.requests.get", boom)

    with pytest.raises(AdapterUnavailable):
        adapter.search("toothpaste")


def test_open_circuit_breaker_raises_adapter_unavailable(settings, monkeypatch):
    settings.SERPAPI_KEY = "test-key"
    adapter = SerpApiGoogleShoppingAdapter()

    def already_open(*args, **kwargs):
        raise pybreaker.CircuitBreakerError("circuit is open")

    monkeypatch.setattr(adapter, "_call_serpapi", already_open)

    with pytest.raises(AdapterUnavailable):
        adapter.search("toothpaste")

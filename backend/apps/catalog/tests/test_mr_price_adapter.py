import pybreaker
import pytest
import requests

from apps.catalog.adapters.base import AdapterUnavailable
from apps.catalog.adapters.mr_price import MrPriceAdapter

pytestmark = pytest.mark.django_db


def test_not_configured_without_a_base_url(settings):
    settings.MR_PRICE_API_BASE_URL = ""
    assert MrPriceAdapter().is_configured() is False


def test_configured_with_a_base_url(settings):
    settings.MR_PRICE_API_BASE_URL = "https://example.test/mrp/search"
    assert MrPriceAdapter().is_configured() is True


def test_search_without_a_base_url_raises_adapter_unavailable(settings):
    settings.MR_PRICE_API_BASE_URL = ""
    with pytest.raises(AdapterUnavailable):
        MrPriceAdapter().search("t-shirt")


def test_normalize_skips_rows_missing_price():
    assert MrPriceAdapter._normalize({"name": "Basic Tee"}) is None


def test_normalize_extracts_colour_and_size():
    raw = {"name": "Basic Tee", "price": 99.99, "category": "Clothing", "colour": "Navy", "size": "M"}
    listing = MrPriceAdapter._normalize(raw)

    assert listing.product_name == "Basic Tee"
    assert listing.retailer_name == "Mr Price"
    assert listing.color == "Navy"
    assert listing.size == "M"
    assert listing.retailer_base_url == "https://www.mrp.com"


def test_search_wraps_request_exceptions_as_adapter_unavailable(settings, monkeypatch):
    settings.MR_PRICE_API_BASE_URL = "https://example.test/mrp/search"
    adapter = MrPriceAdapter()

    def boom(*args, **kwargs):
        raise requests.ConnectionError("no network")

    monkeypatch.setattr("apps.catalog.adapters.mr_price.requests.get", boom)

    with pytest.raises(AdapterUnavailable):
        adapter.search("t-shirt")


def test_open_circuit_breaker_raises_adapter_unavailable(settings, monkeypatch):
    settings.MR_PRICE_API_BASE_URL = "https://example.test/mrp/search"
    adapter = MrPriceAdapter()

    def already_open(*args, **kwargs):
        raise pybreaker.CircuitBreakerError("circuit is open")

    monkeypatch.setattr(adapter, "_call_api", already_open)

    with pytest.raises(AdapterUnavailable):
        adapter.search("t-shirt")

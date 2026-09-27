import pybreaker
import pytest
import requests

from apps.catalog.adapters.base import AdapterUnavailable
from apps.catalog.adapters.serpapi_google_shopping import (
    SerpApiGoogleShoppingAdapter,
    _is_south_african_domain,
)

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


def test_normalize_skips_a_listing_with_a_foreign_cctld():
    raw = {
        "title": "British Biscuits Tin",
        "source": "BritishCravings",
        "extracted_price": 199.00,
        "product_link": "https://www.britishcravings.co.uk/some-product",
    }
    assert SerpApiGoogleShoppingAdapter._normalize(raw) is None


def test_normalize_keeps_a_co_za_listing():
    raw = {
        "title": "Colgate Toothpaste",
        "source": "Takealot",
        "extracted_price": 24.99,
        "product_link": "https://www.makro.co.za/some-product",
    }
    assert SerpApiGoogleShoppingAdapter._normalize(raw) is not None


def test_normalize_keeps_a_listing_with_no_link_at_all():
    """No link means no domain signal either way — abstain, don't guess
    foreign (see the module-level comment on _is_south_african_domain)."""
    raw = {"title": "Colgate Toothpaste", "source": "Some Store", "extracted_price": 24.99}
    assert SerpApiGoogleShoppingAdapter._normalize(raw) is not None


class TestIsSouthAfricanDomain:
    def test_no_url_abstains_as_south_african(self):
        assert _is_south_african_domain(None) is True

    def test_co_za_is_south_african(self):
        assert _is_south_african_domain("https://www.checkers.co.za") is True

    def test_generic_com_abstains_as_south_african(self):
        # takealot.com has no ccTLD at all — nothing to prove it's foreign.
        assert _is_south_african_domain("https://www.takealot.com") is True

    def test_co_uk_is_rejected(self):
        assert _is_south_african_domain("https://www.example.co.uk") is False

    def test_saudi_arabia_sa_is_rejected_not_confused_with_south_africa(self):
        assert _is_south_african_domain("https://www.example.sa") is False


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

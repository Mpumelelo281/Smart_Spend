from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.geo import distance_from_campus_km, resolve_distance_km
from apps.catalog.models import PriceRecord, Product, Retailer

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog(db):
    near = Retailer.objects.create(
        name="Near Store",
        integration_type=Retailer.IntegrationType.SCRAPER,
        base_url="https://near.example",
        store_address="1 Test St",
        latitude=Decimal("-29.8578"),
        longitude=Decimal("31.0206"),
    )
    online = Retailer.objects.create(
        name="Online Store",
        integration_type=Retailer.IntegrationType.API,
        base_url="https://online.example",
    )
    product = Product.objects.create(
        name="Test Deodorant",
        category="Toiletries",
        attributes={"color": "Black", "size": "50ml"},
    )
    now = timezone.now()
    PriceRecord.objects.create(
        product=product, retailer=near, price=Decimal("30.00"), delivery_cost=0, retrieved_at=now
    )
    PriceRecord.objects.create(
        product=product,
        retailer=online,
        price=Decimal("25.00"),
        delivery_cost=Decimal("45.00"),
        retrieved_at=now,
    )
    return {"near": near, "online": online, "product": product}


def test_search_sorts_by_total_landed_cost_ascending_by_default(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/catalog/search/", {"q": "deodorant"})
    assert response.status_code == 200
    names = [r["retailer_name"] for r in response.data["results"]]
    # Near Store: 30.00 total. Online Store: 25.00 + 45.00 = 70.00 total.
    assert names == ["Near Store", "Online Store"]


def test_search_sort_desc_reverses_order(authenticated_client, catalog):
    response = authenticated_client.get(
        "/api/v1/catalog/search/", {"q": "deodorant", "sort": "landed_cost_desc"}
    )
    names = [r["retailer_name"] for r in response.data["results"]]
    assert names == ["Online Store", "Near Store"]


def test_search_filters_by_color(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/catalog/search/", {"color": "Black"})
    assert response.data["count"] == 2

    response = authenticated_client.get("/api/v1/catalog/search/", {"color": "Red"})
    assert response.data["count"] == 0


def test_search_filters_by_size(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/catalog/search/", {"size": "50ml"})
    assert response.data["count"] == 2

    response = authenticated_client.get("/api/v1/catalog/search/", {"size": "100ml"})
    assert response.data["count"] == 0


def test_search_computes_distance_for_physical_store_only(authenticated_client, catalog):
    # conftest.py's student_user fixture sets campus="Steve Biko".
    response = authenticated_client.get("/api/v1/catalog/search/", {"q": "deodorant"})
    by_retailer = {r["retailer_name"]: r["distance_km"] for r in response.data["results"]}

    assert by_retailer["Near Store"] is not None
    assert by_retailer["Online Store"] is None


def test_inactive_retailer_excluded_from_results(authenticated_client, catalog):
    catalog["near"].is_active = False
    catalog["near"].save()

    response = authenticated_client.get("/api/v1/catalog/search/", {"q": "deodorant"})
    names = [r["retailer_name"] for r in response.data["results"]]
    assert names == ["Online Store"]


def test_unknown_campus_yields_no_distance():
    retailer = Retailer(latitude=Decimal("-29.85"), longitude=Decimal("31.02"))
    assert distance_from_campus_km("Some Unlisted Campus", retailer) is None


def test_search_requires_authentication(api_client):
    response = api_client.get("/api/v1/catalog/search/")
    assert response.status_code == 401


def test_browser_geolocation_overrides_campus_lookup(authenticated_client, catalog):
    # Real coordinates a long way from both the campus lookup and the
    # retailer, purely to prove *these* coordinates were used, not the
    # campus fallback.
    response = authenticated_client.get(
        "/api/v1/catalog/search/", {"q": "deodorant", "lat": "-33.9249", "lon": "18.4241"}
    )
    near_result = next(r for r in response.data["results"] if r["retailer_name"] == "Near Store")
    assert float(near_result["distance_km"]) > 1000  # Cape Town to Durban, not campus-to-store


def test_resolve_distance_km_falls_back_on_malformed_coordinates():
    retailer = Retailer(latitude=Decimal("-29.8578"), longitude=Decimal("31.0206"))
    result = resolve_distance_km("Steve Biko", "not-a-number", "31.0", retailer)
    assert result is not None  # fell back to the campus lookup instead of crashing


def test_suggestions_requires_two_characters(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/catalog/search/suggestions/", {"q": "d"})
    assert response.data["results"] == []


def test_suggestions_matches_partial_name(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/catalog/search/suggestions/", {"q": "deo"})
    assert {"name": "Test Deodorant", "category": "Toiletries"} in response.data["results"]

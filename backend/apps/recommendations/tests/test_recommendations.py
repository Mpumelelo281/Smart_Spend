from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import PriceRecord, Product, Retailer
from apps.recommendations.models import Preference, Recommendation

pytestmark = pytest.mark.django_db


@pytest.fixture
def catalog():
    retailer = Retailer.objects.create(
        name="Budget Mart", integration_type=Retailer.IntegrationType.API, base_url="https://budget.example"
    )
    cheap = Product.objects.create(name="Rice 2kg", category="Groceries")
    pricey = Product.objects.create(name="Steak 1kg", category="Groceries")
    other_category = Product.objects.create(name="Notebook", category="Stationery")
    now = timezone.now()
    PriceRecord.objects.create(product=cheap, retailer=retailer, price=Decimal("30.00"), retrieved_at=now)
    PriceRecord.objects.create(product=pricey, retailer=retailer, price=Decimal("120.00"), retrieved_at=now)
    PriceRecord.objects.create(
        product=other_category, retailer=retailer, price=Decimal("10.00"), retrieved_at=now
    )
    return {"retailer": retailer, "cheap": cheap, "pricey": pricey, "other_category": other_category}


def test_no_preferences_falls_back_to_all_categories(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/recommendations/")
    assert response.status_code == 200
    names = [r["product_name"] for r in response.data["results"]]
    assert set(names) == {"Rice 2kg", "Steak 1kg", "Notebook"}


def test_cheapest_ranked_first(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/recommendations/")
    names = [r["product_name"] for r in response.data["results"]]
    assert names.index("Rice 2kg") < names.index("Steak 1kg")


def test_category_preference_narrows_results(authenticated_client, student_user, catalog):
    profile = student_user.student_profile
    Preference.objects.create(profile=profile, pref_type="category", pref_value="Stationery")

    response = authenticated_client.get("/api/v1/recommendations/")
    names = [r["product_name"] for r in response.data["results"]]
    assert names == ["Notebook"]


def test_offer_includes_current_cheapest_listing(authenticated_client, catalog):
    response = authenticated_client.get("/api/v1/recommendations/")
    row = next(r for r in response.data["results"] if r["product_name"] == "Rice 2kg")
    assert row["offer"]["retailer_name"] == "Budget Mart"
    assert Decimal(row["offer"]["total_landed_cost"]) == Decimal("30.00")


def test_feedback_marks_recommendation_and_removes_it_from_next_batch(authenticated_client, catalog):
    first = authenticated_client.get("/api/v1/recommendations/")
    recommendation_id = first.data["results"][0]["recommendation_id"]

    feedback = authenticated_client.post(
        f"/api/v1/recommendations/{recommendation_id}/feedback/", {"was_accepted": True}, format="json"
    )
    assert feedback.status_code == 200
    assert feedback.data["was_accepted"] is True

    second = authenticated_client.get("/api/v1/recommendations/")
    ids = [r["recommendation_id"] for r in second.data["results"]]
    assert recommendation_id not in ids

    recommendation = Recommendation.objects.get(recommendation_id=recommendation_id)
    assert recommendation.was_accepted is True


def test_preferences_crud(authenticated_client):
    create = authenticated_client.post(
        "/api/v1/recommendations/preferences/",
        {"pref_type": "category", "pref_value": "Groceries"},
        format="json",
    )
    assert create.status_code == 201
    preference_id = create.data["preference_id"]

    listing = authenticated_client.get("/api/v1/recommendations/preferences/")
    assert len(listing.data["results"]) == 1

    delete = authenticated_client.delete(f"/api/v1/recommendations/preferences/{preference_id}/")
    assert delete.status_code == 204
    assert not Preference.objects.filter(preference_id=preference_id).exists()


def test_invalid_pref_type_rejected(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/recommendations/preferences/",
        {"pref_type": "colour", "pref_value": "Blue"},
        format="json",
    )
    assert response.status_code == 400


def test_recommendations_require_authentication(api_client):
    response = api_client.get("/api/v1/recommendations/")
    assert response.status_code == 401

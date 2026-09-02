from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import CartItem, PriceRecord, Product, Retailer

pytestmark = pytest.mark.django_db


@pytest.fixture
def priced_product():
    retailer = Retailer.objects.create(
        name="Cart Store", integration_type=Retailer.IntegrationType.SCRAPER, base_url="https://x.example"
    )
    product = Product.objects.create(name="Cart Item", category="Test")
    PriceRecord.objects.create(
        product=product,
        retailer=retailer,
        price=Decimal("50.00"),
        delivery_cost=Decimal("10.00"),
        retrieved_at=timezone.now(),
    )
    return product, retailer


def _cart_payload(product, retailer, quantity=None):
    payload = {"product_id": str(product.product_id), "retailer_id": str(retailer.retailer_id)}
    if quantity is not None:
        payload["quantity"] = quantity
    return payload


def test_add_to_cart_snapshots_current_price(authenticated_client, priced_product, student_user):
    product, retailer = priced_product
    response = authenticated_client.post("/api/v1/catalog/cart/", _cart_payload(product, retailer))

    assert response.status_code == 201
    item = CartItem.objects.get(profile__user=student_user)
    assert item.price == Decimal("50.00")
    assert item.delivery_cost == Decimal("10.00")
    assert item.quantity == 1


def test_adding_same_item_twice_increments_quantity(authenticated_client, priced_product):
    product, retailer = priced_product
    payload = _cart_payload(product, retailer)

    authenticated_client.post("/api/v1/catalog/cart/", payload)
    authenticated_client.post("/api/v1/catalog/cart/", payload)

    assert CartItem.objects.count() == 1
    assert CartItem.objects.get().quantity == 2


def test_cart_list_includes_total(authenticated_client, priced_product):
    product, retailer = priced_product
    authenticated_client.post("/api/v1/catalog/cart/", _cart_payload(product, retailer, quantity=2))

    response = authenticated_client.get("/api/v1/catalog/cart/")
    assert response.status_code == 200
    # 2 x R50.00 + R10.00 delivery = R110.00
    assert Decimal(response.data["cart_total"]) == Decimal("110.00")
    assert response.data["results"][0]["quantity"] == 2


def test_add_to_cart_without_a_price_record_fails(authenticated_client):
    retailer = Retailer.objects.create(
        name="No Price Store", integration_type=Retailer.IntegrationType.API, base_url="https://y.example"
    )
    product = Product.objects.create(name="Unpriced Item", category="Test")

    response = authenticated_client.post("/api/v1/catalog/cart/", _cart_payload(product, retailer))
    assert response.status_code == 400


def test_update_cart_item_quantity(authenticated_client, priced_product):
    product, retailer = priced_product
    add = authenticated_client.post("/api/v1/catalog/cart/", _cart_payload(product, retailer))
    item_id = add.data["cart_item_id"]

    response = authenticated_client.patch(f"/api/v1/catalog/cart/{item_id}/", {"quantity": 5})
    assert response.status_code == 200
    assert response.data["quantity"] == 5


def test_remove_cart_item(authenticated_client, priced_product):
    product, retailer = priced_product
    add = authenticated_client.post("/api/v1/catalog/cart/", _cart_payload(product, retailer))
    item_id = add.data["cart_item_id"]

    response = authenticated_client.delete(f"/api/v1/catalog/cart/{item_id}/")
    assert response.status_code == 204
    assert CartItem.objects.count() == 0


def test_cart_isolated_per_student(api_client, priced_product):
    from apps.accounts.models import StudentProfile, User
    from rest_framework_simplejwt.tokens import RefreshToken

    product, retailer = priced_product
    other = User.objects.create_user(email="other@dut4life.ac.za", password="Correct-Horse-9!")
    other.email_verified = True
    other.status = User.Status.ACTIVE
    other.save()
    StudentProfile.objects.create(user=other, campus="City")

    token = RefreshToken.for_user(other)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    api_client.post("/api/v1/catalog/cart/", _cart_payload(product, retailer))

    response = api_client.get("/api/v1/catalog/cart/")
    assert len(response.data["results"]) == 1  # only this student's own item


def test_cart_requires_authentication(api_client):
    response = api_client.get("/api/v1/catalog/cart/")
    assert response.status_code == 401

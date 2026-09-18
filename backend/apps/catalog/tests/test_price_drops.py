from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import CartItem, PriceRecord, Product, Retailer
from apps.catalog.tasks import check_price_drops
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def cart_item(student_user):
    retailer = Retailer.objects.create(
        name="Budget Mart", integration_type=Retailer.IntegrationType.API, base_url="https://budget.example"
    )
    product = Product.objects.create(name="Rice 2kg", category="Groceries")
    PriceRecord.objects.create(
        product=product, retailer=retailer, price=Decimal("50.00"), retrieved_at=timezone.now()
    )
    return CartItem.objects.create(
        profile=student_user.student_profile,
        product=product,
        retailer=retailer,
        price=Decimal("50.00"),
        delivery_cost=Decimal("0.00"),
    )


def _undercut(item, price):
    PriceRecord.objects.create(
        product=item.product, retailer=item.retailer, price=Decimal(price), retrieved_at=timezone.now()
    )


def test_no_alert_when_price_unchanged(cart_item):
    check_price_drops()
    assert not Notification.objects.filter(notif_type=Notification.NotifType.PRICE_DROP).exists()


def test_alert_fires_when_price_drops(cart_item):
    _undercut(cart_item, "35.00")

    check_price_drops()

    notification = Notification.objects.get(notif_type=Notification.NotifType.PRICE_DROP)
    assert notification.profile == cart_item.profile
    assert notification.related_product == cart_item.product
    assert "Rice 2kg" in notification.message


def test_no_duplicate_alert_while_previous_one_is_unread(cart_item):
    _undercut(cart_item, "35.00")
    check_price_drops()
    _undercut(cart_item, "30.00")
    check_price_drops()

    assert Notification.objects.filter(notif_type=Notification.NotifType.PRICE_DROP).count() == 1


def test_new_alert_allowed_after_previous_one_dismissed(cart_item):
    _undercut(cart_item, "35.00")
    check_price_drops()
    Notification.objects.filter(notif_type=Notification.NotifType.PRICE_DROP).update(is_read=True)

    _undercut(cart_item, "20.00")
    check_price_drops()

    assert Notification.objects.filter(notif_type=Notification.NotifType.PRICE_DROP).count() == 2


def test_no_price_record_is_skipped_gracefully(student_user):
    product = Product.objects.create(name="Ghost Product", category="Groceries")
    retailer = Retailer.objects.create(
        name="Vanished Store", integration_type=Retailer.IntegrationType.API, base_url="https://x.example"
    )
    CartItem.objects.create(
        profile=student_user.student_profile,
        product=product,
        retailer=retailer,
        price=Decimal("10.00"),
    )
    PriceRecord.objects.filter(product=product).delete()

    check_price_drops()  # must not raise

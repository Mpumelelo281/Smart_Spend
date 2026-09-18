import uuid

import pytest

from apps.budgets.tasks import dispatch_threshold_check
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


def test_dispatch_threshold_check_ignores_missing_category():
    # A category deleted between the transaction being logged and the task
    # running — must not raise.
    dispatch_threshold_check(uuid.uuid4())


def test_transaction_create_falls_back_to_sync_when_broker_is_unreachable(
    authenticated_client, student_user, monkeypatch
):
    """Regression: with no Celery broker reachable (the real failure mode
    in a local dev setup with no Redis/worker running), `.delay()` used to
    fail silently and the alert never fired at all — see
    TransactionSerializer.create(). It must now run the check inline
    instead of dropping it.
    """
    monkeypatch.setattr(
        "apps.budgets.serializers.dispatch_threshold_check.delay",
        lambda *a, **k: (_ for _ in ()).throw(ConnectionError("no broker reachable")),
    )

    create = authenticated_client.post(
        "/api/v1/budgets/",
        {"month": 6, "year": 2026, "categories": [{"name": "Food", "allocated_amount": "100.00"}]},
        format="json",
    )
    category_id = create.data["categories"][0]["category_id"]

    response = authenticated_client.post(
        "/api/v1/budgets/transactions/",
        {"category": category_id, "amount": "90.00", "purchase_date": "2026-06-05"},
        format="json",
    )

    assert response.status_code == 201
    assert Notification.objects.filter(profile__user=student_user).exists()

"""Rule 10: alert at 80% of a category allocation, and again when exceeded."""

import pytest

from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


def _create_budget(authenticated_client, allocated="100.00"):
    authenticated_client.post(
        "/api/v1/budgets/",
        {"month": 6, "year": 2026, "categories": [{"name": "Food", "allocated_amount": allocated}]},
        format="json",
    )
    category_id = authenticated_client.get("/api/v1/budgets/", format="json").data["results"][0][
        "categories"
    ][0]["category_id"]
    return category_id


def _log_transaction(authenticated_client, category_id, amount):
    return authenticated_client.post(
        "/api/v1/budgets/transactions/",
        {"category": category_id, "amount": amount, "purchase_date": "2026-06-05"},
        format="json",
    )


def test_no_notification_below_threshold(authenticated_client, student_user):
    category_id = _create_budget(authenticated_client)
    _log_transaction(authenticated_client, category_id, "50.00")  # 50% of 100

    assert not Notification.objects.filter(profile__user=student_user).exists()


def test_notification_fires_at_80_percent(authenticated_client, student_user):
    category_id = _create_budget(authenticated_client)
    _log_transaction(authenticated_client, category_id, "80.00")

    notification = Notification.objects.get(profile__user=student_user)
    assert notification.notif_type == Notification.NotifType.BUDGET_THRESHOLD_80
    assert "Food" in notification.message
    assert "80" in notification.message or "R20" in notification.message


def test_notification_fires_again_when_exceeded(authenticated_client, student_user):
    category_id = _create_budget(authenticated_client)
    _log_transaction(authenticated_client, category_id, "80.00")
    _log_transaction(authenticated_client, category_id, "30.00")  # now 110/100

    types = set(
        Notification.objects.filter(profile__user=student_user).values_list("notif_type", flat=True)
    )
    assert types == {Notification.NotifType.BUDGET_THRESHOLD_80, Notification.NotifType.BUDGET_EXCEEDED}


def test_threshold_notification_not_duplicated(authenticated_client, student_user):
    category_id = _create_budget(authenticated_client)
    _log_transaction(authenticated_client, category_id, "80.00")
    _log_transaction(authenticated_client, category_id, "1.00")  # still >= 80%, same threshold

    count = Notification.objects.filter(
        profile__user=student_user, notif_type=Notification.NotifType.BUDGET_THRESHOLD_80
    ).count()
    assert count == 1


def test_notification_list_and_mark_read(authenticated_client, student_user):
    category_id = _create_budget(authenticated_client)
    _log_transaction(authenticated_client, category_id, "80.00")

    response = authenticated_client.get("/api/v1/notifications/")
    assert response.status_code == 200
    assert len(response.data) == 1
    notification_id = response.data[0]["notification_id"]
    assert response.data[0]["is_read"] is False

    mark_response = authenticated_client.post(f"/api/v1/notifications/{notification_id}/read/")
    assert mark_response.status_code == 200
    assert mark_response.data["is_read"] is True


def test_notifications_require_authentication(api_client):
    response = api_client.get("/api/v1/notifications/")
    assert response.status_code == 401

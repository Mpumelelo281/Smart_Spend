"""Rule 1: allocations must not exceed the allowance, enforced server-side.

These hit the API directly (not the serializer in isolation) so the test
also proves the rule survives a client that skips its own preview check.
"""

import pytest

from apps.budgets.models import Budget

pytestmark = pytest.mark.django_db


def _payload(categories):
    return {"month": 3, "year": 2026, "categories": categories}


def test_allocations_within_allowance_are_accepted(authenticated_client, student_user):
    response = authenticated_client.post(
        "/api/v1/budgets/",
        _payload(
            [
                {"name": "Food", "allocated_amount": "800.00"},
                {"name": "Data", "allocated_amount": "300.00"},
                {"name": "Toiletries", "allocated_amount": "200.00"},
            ]
        ),
        format="json",
    )

    assert response.status_code == 201
    budget = Budget.objects.get(profile__user=student_user)
    assert budget.total_allocated == 1300
    assert budget.categories.count() == 3


def test_allocations_exceeding_allowance_are_rejected(authenticated_client, student_user):
    response = authenticated_client.post(
        "/api/v1/budgets/",
        _payload(
            [
                {"name": "Food", "allocated_amount": "1000.00"},
                {"name": "Data", "allocated_amount": "700.00"},
            ]
        ),
        format="json",
    )

    assert response.status_code == 400
    assert "categories" in response.data
    assert not Budget.objects.filter(profile__user=student_user).exists()


def test_allocations_exactly_at_allowance_are_accepted(authenticated_client, student_user):
    response = authenticated_client.post(
        "/api/v1/budgets/",
        _payload([{"name": "Food", "allocated_amount": "1650.00"}]),
        format="json",
    )

    assert response.status_code == 201


def test_duplicate_category_names_rejected(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/budgets/",
        _payload(
            [
                {"name": "Food", "allocated_amount": "100.00"},
                {"name": "food", "allocated_amount": "50.00"},
            ]
        ),
        format="json",
    )
    assert response.status_code == 400


def test_negative_allocation_rejected(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/budgets/", _payload([{"name": "Food", "allocated_amount": "-10.00"}]), format="json"
    )
    assert response.status_code == 400


def test_second_budget_same_month_rejected(authenticated_client, student_user):
    authenticated_client.post(
        "/api/v1/budgets/", _payload([{"name": "Food", "allocated_amount": "100.00"}]), format="json"
    )
    response = authenticated_client.post(
        "/api/v1/budgets/", _payload([{"name": "Data", "allocated_amount": "100.00"}]), format="json"
    )
    assert response.status_code == 400
    assert Budget.objects.filter(profile__user=student_user).count() == 1


def test_unauthenticated_request_rejected(api_client):
    response = api_client.post(
        "/api/v1/budgets/", _payload([{"name": "Food", "allocated_amount": "100.00"}]), format="json"
    )
    assert response.status_code == 401

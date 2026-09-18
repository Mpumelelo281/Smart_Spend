"""The "Other" option in the log-expense form: a student adding a category
to their own existing budget on the fly, for spend that doesn't fit
anything they pre-allocated (see BudgetCategoryCreateSerializer).
"""

import pytest

from apps.budgets.models import Budget, BudgetCategory

pytestmark = pytest.mark.django_db


def _create_budget(authenticated_client, allocated="800.00"):
    response = authenticated_client.post(
        "/api/v1/budgets/",
        {"month": 4, "year": 2026, "categories": [{"name": "Food", "allocated_amount": allocated}]},
        format="json",
    )
    return response.data["budget_id"]


def test_adhoc_category_created_at_zero_allocation(authenticated_client, student_user):
    budget_id = _create_budget(authenticated_client)

    response = authenticated_client.post(
        f"/api/v1/budgets/{budget_id}/categories/", {"name": "Textbooks"}, format="json"
    )

    assert response.status_code == 201
    assert response.data["name"] == "Textbooks"
    assert response.data["allocated_amount"] == "0.00"

    budget = Budget.objects.get(pk=budget_id)
    assert budget.total_allocated == 800  # unaffected by the R0 ad-hoc category
    assert BudgetCategory.objects.filter(budget=budget, name="Textbooks").exists()


def test_adhoc_category_reuses_existing_case_insensitive_match(authenticated_client):
    budget_id = _create_budget(authenticated_client)

    first = authenticated_client.post(
        f"/api/v1/budgets/{budget_id}/categories/", {"name": "Transport"}, format="json"
    )
    second = authenticated_client.post(
        f"/api/v1/budgets/{budget_id}/categories/", {"name": "transport"}, format="json"
    )

    assert first.status_code == 201
    assert second.status_code == 201
    assert first.data["category_id"] == second.data["category_id"]
    assert BudgetCategory.objects.filter(budget_id=budget_id, name__iexact="transport").count() == 1


def test_adhoc_category_can_be_used_to_log_a_transaction(authenticated_client):
    budget_id = _create_budget(authenticated_client)
    category = authenticated_client.post(
        f"/api/v1/budgets/{budget_id}/categories/", {"name": "Stationery"}, format="json"
    ).data

    response = authenticated_client.post(
        "/api/v1/budgets/transactions/",
        {"category": category["category_id"], "amount": "45.00", "purchase_date": "2026-04-10"},
        format="json",
    )
    assert response.status_code == 201


def test_adhoc_category_rejects_blank_name(authenticated_client):
    budget_id = _create_budget(authenticated_client)

    response = authenticated_client.post(
        f"/api/v1/budgets/{budget_id}/categories/", {"name": "   "}, format="json"
    )
    assert response.status_code == 400


def test_adhoc_category_rejects_another_students_budget(authenticated_client, django_user_model):
    from apps.accounts.models import StudentProfile

    other_user = django_user_model.objects.create_user(
        email="other@dut4life.ac.za", password="Correct-Horse-9!"
    )
    other_user.email_verified = True
    other_user.status = django_user_model.Status.ACTIVE
    other_user.save()
    other_profile = StudentProfile.objects.create(user=other_user, campus="Ritson", disbursement_day=1)
    other_budget = Budget.objects.create(profile=other_profile, month=4, year=2026, total_allocated=0)

    response = authenticated_client.post(
        f"/api/v1/budgets/{other_budget.pk}/categories/", {"name": "Snacks"}, format="json"
    )
    assert response.status_code == 404


def test_adhoc_category_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/budgets/00000000-0000-0000-0000-000000000000/categories/", {"name": "Snacks"}, format="json"
    )
    assert response.status_code == 401

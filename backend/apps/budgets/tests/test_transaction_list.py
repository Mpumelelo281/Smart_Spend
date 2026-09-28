import pytest

pytestmark = pytest.mark.django_db


def _create_budget(client, month=3, year=2026, allocated="500.00"):
    response = client.post(
        "/api/v1/budgets/",
        {"month": month, "year": year, "categories": [{"name": "Food", "allocated_amount": allocated}]},
        format="json",
    )
    return response.data["budget_id"], response.data["categories"][0]["category_id"]


def test_lists_transactions_newest_first_with_category_name(authenticated_client):
    budget_id, category_id = _create_budget(authenticated_client)
    authenticated_client.post(
        "/api/v1/budgets/transactions/",
        {"category": category_id, "amount": "20.00", "purchase_date": "2026-03-01", "description": "Bread"},
        format="json",
    )
    authenticated_client.post(
        "/api/v1/budgets/transactions/",
        {"category": category_id, "amount": "45.00", "purchase_date": "2026-03-10", "description": "Milk"},
        format="json",
    )

    response = authenticated_client.get(f"/api/v1/budgets/{budget_id}/transactions/")

    assert response.status_code == 200
    assert [row["description"] for row in response.data] == ["Milk", "Bread"]
    assert response.data[0]["category_name"] == "Food"
    assert str(response.data[0]["category"]) == category_id


def test_empty_budget_returns_empty_list(authenticated_client):
    budget_id, _ = _create_budget(authenticated_client)
    response = authenticated_client.get(f"/api/v1/budgets/{budget_id}/transactions/")
    assert response.status_code == 200
    assert response.data == []


def test_404_for_a_budget_that_is_not_the_students_own(authenticated_client, student_user):
    from apps.accounts.models import StudentProfile, User
    from apps.budgets.models import Budget

    other = User.objects.create_user(email="other@dut4life.ac.za", password="Correct-Horse-9!")
    other_profile = StudentProfile.objects.create(user=other, campus="ML Sultan")
    other_budget = Budget.objects.create(profile=other_profile, month=1, year=2020, total_allocated="0")

    response = authenticated_client.get(f"/api/v1/budgets/{other_budget.budget_id}/transactions/")
    assert response.status_code == 404


def test_requires_authentication(api_client):
    response = api_client.get("/api/v1/budgets/00000000-0000-0000-0000-000000000000/transactions/")
    assert response.status_code == 401

"""These tests monkeypatch get_queryset() rather than hit the real
`reporting` database connection: CategorySpendSummary/BudgetUtilizationSummary
are unmanaged models over materialised views created by raw SQL
(infra/sql/002_reporting_views.sql), which nothing in the Django test
runner creates (see smartspend/db_router.py — the reporting app_label is
deliberately excluded from allow_migrate). What belongs in this test suite
is the RBAC layer and response shape, not PostgreSQL's own view/grant
machinery — that's infra, verified by applying the SQL itself, not by a
Django unit test.
"""

from decimal import Decimal

import pytest
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import StudentProfile, User
from apps.reporting import views
from apps.reporting.models import BudgetUtilizationSummary, CategorySpendSummary

pytestmark = pytest.mark.django_db


def _client_for_role(api_client, role, email):
    user = User.objects.create_user(email=email, password="Correct-Horse-9!")
    user.role = role
    user.email_verified = True
    user.status = User.Status.ACTIVE
    user.save()
    StudentProfile.objects.create(user=user, campus="City", disbursement_day=1)
    token = RefreshToken.for_user(user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client


@pytest.fixture
def student_services_client(api_client):
    return _client_for_role(api_client, User.Role.STUDENT_SERVICES, "officer@dut4life.ac.za")


@pytest.fixture
def administrator_client(api_client):
    return _client_for_role(api_client, User.Role.ADMINISTRATOR, "admin@dut4life.ac.za")


def test_students_cannot_access_category_spend_report(authenticated_client, monkeypatch):
    monkeypatch.setattr(views.CategorySpendReportView, "get_queryset", lambda self: [])
    response = authenticated_client.get("/api/v1/reporting/category-spend/")
    assert response.status_code == 403


def test_anonymous_cannot_access_reports(api_client):
    response = api_client.get("/api/v1/reporting/category-spend/")
    assert response.status_code == 401


def test_student_services_officer_sees_aggregated_rows(student_services_client, monkeypatch):
    row = CategorySpendSummary(
        id=1,
        campus="Steve Biko",
        year=2026,
        month=6,
        category_name="Groceries",
        student_count=12,
        total_spent=Decimal("6000.00"),
        avg_transaction_amount=Decimal("50.00"),
        total_allocated=Decimal("7200.00"),
    )
    monkeypatch.setattr(views.CategorySpendReportView, "get_queryset", lambda self: [row])

    response = student_services_client.get("/api/v1/reporting/category-spend/")
    assert response.status_code == 200
    assert response.data[0]["student_count"] == 12
    assert response.data[0]["category_name"] == "Groceries"
    # Row-level student identifiers must never leak through this endpoint.
    assert "profile" not in response.data[0]
    assert "user" not in response.data[0]


def test_administrator_can_access_budget_utilization_report(administrator_client, monkeypatch):
    row = BudgetUtilizationSummary(
        id=1,
        campus="Steve Biko",
        year=2026,
        month=6,
        student_count=15,
        total_allocated=Decimal("24750.00"),
        total_spent=Decimal("19000.00"),
    )
    monkeypatch.setattr(views.BudgetUtilizationReportView, "get_queryset", lambda self: [row])

    response = administrator_client.get("/api/v1/reporting/budget-utilization/")
    assert response.status_code == 200
    assert response.data[0]["total_spent"] == "19000.00"

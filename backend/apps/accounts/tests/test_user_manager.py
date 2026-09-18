import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db


def test_create_superuser_stores_the_email_lowercased():
    user = User.objects.create_superuser(email="Admin.Person@Example.COM", password="Correct-Horse-9!")
    assert user.email == "admin.person@example.com"


def test_create_user_stores_the_email_lowercased():
    user = User.objects.create_user(email="Thabo@DUT4LIFE.ac.za", password="Correct-Horse-9!")
    assert user.email == "thabo@dut4life.ac.za"


def test_login_works_for_a_superuser_created_with_a_capitalised_email(api_client):
    """Regression: createsuperuser used to keep the local part's capitals,
    but login lowercases the whole address, so this account could never
    authenticate.
    """
    User.objects.create_superuser(email="Admin@Example.com", password="Correct-Horse-9!")

    response = api_client.post(
        "/api/v1/auth/login/",
        {"email": "Admin@Example.com", "password": "Correct-Horse-9!"},
        format="json",
    )

    assert response.status_code == 200

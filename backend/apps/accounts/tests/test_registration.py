import pytest
from django.core import mail

from apps.accounts.models import StudentProfile, User

pytestmark = pytest.mark.django_db


def _register(api_client, **overrides):
    payload = {
        "email": "nomvula@dut4life.ac.za",
        "password": "Correct-Horse-9!",
        "campus": "ML Sultan",
        "residence": "Alan Taylor",
        "disbursement_day": 1,
    }
    payload.update(overrides)
    return api_client.post("/api/v1/auth/register/", payload, format="json")


def test_registration_creates_pending_user_and_profile(api_client):
    response = _register(api_client)

    assert response.status_code == 201
    user = User.objects.get(email="nomvula@dut4life.ac.za")
    assert user.status == User.Status.PENDING_VERIFICATION
    assert user.email_verified is False
    assert StudentProfile.objects.filter(user=user).exists()
    assert len(mail.outbox) == 1
    assert str(user.email_verification_token) in mail.outbox[0].body


def test_registration_rejects_non_dut_email(api_client):
    response = _register(api_client, email="nomvula@gmail.com")

    assert response.status_code == 400
    assert not User.objects.filter(email="nomvula@gmail.com").exists()


def test_registration_rejects_duplicate_email(api_client):
    _register(api_client)
    response = _register(api_client)

    assert response.status_code == 400


def test_verify_email_activates_account(api_client):
    _register(api_client)
    user = User.objects.get(email="nomvula@dut4life.ac.za")

    response = api_client.post(
        "/api/v1/auth/verify-email/", {"token": str(user.email_verification_token)}, format="json"
    )

    user.refresh_from_db()
    assert response.status_code == 200
    assert user.email_verified is True
    assert user.status == User.Status.ACTIVE

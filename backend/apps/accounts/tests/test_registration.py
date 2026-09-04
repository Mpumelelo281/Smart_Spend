import pytest
from django.core import mail

from apps.accounts.models import AuditLog, StudentProfile, User

pytestmark = pytest.mark.django_db


def _register(api_client, **overrides):
    payload = {
        "email": "nomvula@dut4life.ac.za",
        "password": "Correct-Horse-9!",
        "campus": "ML Sultan",
        "residence": "Alan Taylor",
        "disbursement_day": 1,
        "popia_consent": True,
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


def test_registration_records_popia_consent_timestamp(api_client):
    _register(api_client)

    user = User.objects.get(email="nomvula@dut4life.ac.za")
    assert user.popia_consent_at is not None
    assert AuditLog.objects.filter(actor=user, action="POPIA_CONSENT_GIVEN").exists()


def test_registration_rejects_missing_popia_consent(api_client):
    response = _register(api_client, popia_consent=False)

    assert response.status_code == 400
    assert not User.objects.filter(email="nomvula@dut4life.ac.za").exists()


def test_registration_rejects_absent_popia_consent_field(api_client):
    payload = {
        "email": "nomvula@dut4life.ac.za",
        "password": "Correct-Horse-9!",
        "campus": "ML Sultan",
    }
    response = api_client.post("/api/v1/auth/register/", payload, format="json")

    assert response.status_code == 400
    assert not User.objects.filter(email="nomvula@dut4life.ac.za").exists()


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


def test_resend_verification_rotates_token_and_sends_new_email(api_client):
    _register(api_client)
    user = User.objects.get(email="nomvula@dut4life.ac.za")
    original_token = user.email_verification_token

    response = api_client.post(
        "/api/v1/auth/resend-verification/", {"email": user.email}, format="json"
    )

    assert response.status_code == 200
    user.refresh_from_db()
    assert user.email_verification_token != original_token
    assert len(mail.outbox) == 2
    assert str(user.email_verification_token) in mail.outbox[1].body

    # The old link no longer verifies the account once a new one is issued.
    stale = api_client.post(
        "/api/v1/auth/verify-email/", {"token": str(original_token)}, format="json"
    )
    assert stale.status_code == 404


def test_resend_verification_is_silent_for_unknown_email(api_client):
    response = api_client.post(
        "/api/v1/auth/resend-verification/", {"email": "nobody@dut4life.ac.za"}, format="json"
    )
    assert response.status_code == 200
    assert len(mail.outbox) == 0


def test_resend_verification_is_silent_for_already_verified_email(api_client):
    _register(api_client)
    user = User.objects.get(email="nomvula@dut4life.ac.za")
    user.email_verified = True
    user.save()

    response = api_client.post(
        "/api/v1/auth/resend-verification/", {"email": user.email}, format="json"
    )

    assert response.status_code == 200
    assert len(mail.outbox) == 1

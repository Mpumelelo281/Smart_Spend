import pyotp
import pytest

pytestmark = pytest.mark.django_db


def test_first_login_requires_mfa_enrolment(api_client, student_user):
    response = api_client.post(
        "/api/v1/auth/login/", {"email": student_user.email, "password": "Correct-Horse-9!"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["mfa_setup_required"] is True
    assert "setup_token" in response.data
    assert "qr_code_base64" in response.data


def test_login_rejects_wrong_password(api_client, student_user):
    response = api_client.post(
        "/api/v1/auth/login/", {"email": student_user.email, "password": "wrong"}, format="json"
    )
    assert response.status_code == 400


def test_mfa_setup_confirm_issues_tokens_and_enables_mfa(api_client, student_user):
    login = api_client.post(
        "/api/v1/auth/login/", {"email": student_user.email, "password": "Correct-Horse-9!"}, format="json"
    )
    setup_token = login.data["setup_token"]

    # Recover the secret the same way the client would have (from the
    # provisioning URI), to generate a valid code without touching internals.
    from urllib.parse import parse_qs, urlparse

    secret = parse_qs(urlparse(login.data["provisioning_uri"]).query)["secret"][0]
    code = pyotp.TOTP(secret).now()

    response = api_client.post(
        "/api/v1/auth/mfa/setup/confirm/", {"setup_token": setup_token, "code": code}, format="json"
    )

    assert response.status_code == 200
    assert "access" in response.data and "refresh" in response.data
    student_user.refresh_from_db()
    assert student_user.mfa_enabled is True


def test_second_login_challenges_totp_not_setup(api_client, student_user):
    student_user.mfa_secret = pyotp.random_base32()
    student_user.mfa_enabled = True
    student_user.save()

    response = api_client.post(
        "/api/v1/auth/login/", {"email": student_user.email, "password": "Correct-Horse-9!"}, format="json"
    )

    assert response.status_code == 200
    assert response.data["mfa_required"] is True
    assert "login_token" in response.data


def test_mfa_verify_wrong_code_rejected(api_client, student_user):
    student_user.mfa_secret = pyotp.random_base32()
    student_user.mfa_enabled = True
    student_user.save()

    login = api_client.post(
        "/api/v1/auth/login/", {"email": student_user.email, "password": "Correct-Horse-9!"}, format="json"
    )
    response = api_client.post(
        "/api/v1/auth/mfa/verify/",
        {"login_token": login.data["login_token"], "code": "000000"},
        format="json",
    )

    assert response.status_code == 401


def test_mfa_reset_requires_correct_password(authenticated_client, student_user):
    student_user.mfa_secret = pyotp.random_base32()
    student_user.mfa_enabled = True
    student_user.save()

    response = authenticated_client.post(
        "/api/v1/auth/mfa/reset/", {"current_password": "wrong-password"}, format="json"
    )

    assert response.status_code == 400
    student_user.refresh_from_db()
    assert student_user.mfa_enabled is True


def test_mfa_reset_clears_enrolment_and_requires_setup_again(authenticated_client, student_user):
    student_user.mfa_secret = pyotp.random_base32()
    student_user.mfa_enabled = True
    student_user.save()

    response = authenticated_client.post(
        "/api/v1/auth/mfa/reset/", {"current_password": "Correct-Horse-9!"}, format="json"
    )
    assert response.status_code == 200

    student_user.refresh_from_db()
    assert student_user.mfa_enabled is False
    assert student_user.mfa_secret == ""

    login = authenticated_client.post(
        "/api/v1/auth/login/", {"email": student_user.email, "password": "Correct-Horse-9!"}, format="json"
    )
    assert login.data["mfa_setup_required"] is True


def test_mfa_reset_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/auth/mfa/reset/", {"current_password": "Correct-Horse-9!"}, format="json"
    )
    assert response.status_code == 401

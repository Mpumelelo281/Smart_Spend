import pytest
from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

pytestmark = pytest.mark.django_db


def test_patch_profile_updates_editable_fields(authenticated_client, student_user):
    response = authenticated_client.patch(
        "/api/v1/auth/me/", {"campus": "Ritson", "residence": "New Res"}, format="json"
    )
    assert response.status_code == 200
    assert response.data["profile"]["campus"] == "Ritson"
    assert response.data["profile"]["residence"] == "New Res"

    student_user.student_profile.refresh_from_db()
    assert student_user.student_profile.campus == "Ritson"


def test_patch_profile_ignores_allowance_amount(authenticated_client, student_user):
    student_user.student_profile.refresh_from_db()
    original = student_user.student_profile.allowance_amount

    response = authenticated_client.patch("/api/v1/auth/me/", {"allowance_amount": "9999.00"}, format="json")
    assert response.status_code == 200

    student_user.student_profile.refresh_from_db()
    assert student_user.student_profile.allowance_amount == original


def test_change_password_requires_correct_current_password(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/auth/change-password/",
        {"current_password": "wrong-password", "new_password": "New-Password-9!"},
        format="json",
    )
    assert response.status_code == 400


def test_change_password_success(authenticated_client, student_user):
    response = authenticated_client.post(
        "/api/v1/auth/change-password/",
        {"current_password": "Correct-Horse-9!", "new_password": "New-Password-9!"},
        format="json",
    )
    assert response.status_code == 200

    student_user.refresh_from_db()
    assert student_user.check_password("New-Password-9!")


def test_change_password_requires_authentication(api_client):
    response = api_client.post(
        "/api/v1/auth/change-password/",
        {"current_password": "x", "new_password": "New-Password-9!"},
        format="json",
    )
    assert response.status_code == 401


def test_password_reset_request_sends_email_for_known_user(api_client, student_user):
    response = api_client.post(
        "/api/v1/auth/password-reset/request/", {"email": student_user.email}, format="json"
    )
    assert response.status_code == 200
    assert len(mail.outbox) == 1
    assert "reset-password" in mail.outbox[0].body


def test_password_reset_request_is_silent_for_unknown_email(api_client):
    response = api_client.post(
        "/api/v1/auth/password-reset/request/", {"email": "nobody@dut4life.ac.za"}, format="json"
    )
    # Same 200 + generic message either way — no user enumeration.
    assert response.status_code == 200
    assert len(mail.outbox) == 0


def test_password_reset_confirm_with_valid_token(api_client, student_user):
    uid = urlsafe_base64_encode(force_bytes(student_user.pk))
    token = default_token_generator.make_token(student_user)

    response = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "Brand-New-Pass9!"},
        format="json",
    )
    assert response.status_code == 200

    student_user.refresh_from_db()
    assert student_user.check_password("Brand-New-Pass9!")


def test_password_reset_confirm_rejects_bad_token(api_client, student_user):
    uid = urlsafe_base64_encode(force_bytes(student_user.pk))

    response = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {"uid": uid, "token": "not-a-real-token", "new_password": "Brand-New-Pass9!"},
        format="json",
    )
    assert response.status_code == 400


def test_password_reset_token_is_single_use(api_client, student_user):
    uid = urlsafe_base64_encode(force_bytes(student_user.pk))
    token = default_token_generator.make_token(student_user)

    first = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "Brand-New-Pass9!"},
        format="json",
    )
    assert first.status_code == 200

    second = api_client.post(
        "/api/v1/auth/password-reset/confirm/",
        {"uid": uid, "token": token, "new_password": "Another-Pass9!"},
        format="json",
    )
    assert second.status_code == 400

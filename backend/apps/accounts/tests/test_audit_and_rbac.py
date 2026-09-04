import pytest

from apps.accounts.models import AuditLog

pytestmark = pytest.mark.django_db


def test_registration_writes_an_audit_entry(api_client):
    api_client.post(
        "/api/v1/auth/register/",
        {
            "email": "sipho@dut4life.ac.za",
            "password": "Correct-Horse-9!",
            "campus": "City",
            "popia_consent": True,
        },
        format="json",
    )
    assert AuditLog.objects.filter(action="USER_REGISTERED").exists()


def test_failed_login_writes_an_audit_entry(api_client, student_user):
    api_client.post("/api/v1/auth/login/", {"email": student_user.email, "password": "wrong"}, format="json")
    assert AuditLog.objects.filter(action="LOGIN_FAILED").exists()


def test_audit_log_is_append_only():
    entry = AuditLog.objects.create(action="TEST_ACTION")

    with pytest.raises(RuntimeError):
        entry.action = "MUTATED"
        entry.save()

    with pytest.raises(RuntimeError):
        entry.delete()


def test_me_endpoint_requires_authentication(api_client):
    response = api_client.get("/api/v1/auth/me/")
    assert response.status_code == 401


def test_me_endpoint_returns_profile(authenticated_client, student_user):
    response = authenticated_client.get("/api/v1/auth/me/")
    assert response.status_code == 200
    assert response.data["email"] == student_user.email
    assert response.data["profile"]["campus"] == "Steve Biko"

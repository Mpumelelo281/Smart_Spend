import pytest

from apps.accounts.models import User

pytestmark = pytest.mark.django_db

PASSWORD = "Correct-Horse-9!"


@pytest.fixture
def unverified_user():
    # create_user() leaves new accounts PENDING_VERIFICATION / unverified.
    return User.objects.create_user(email="pending@dut4life.ac.za", password=PASSWORD)


def _login(api_client, email, password):
    return api_client.post("/api/v1/auth/login/", {"email": email, "password": password}, format="json")


def test_unverified_account_with_correct_password_is_told_to_verify(api_client, unverified_user):
    """Regression: this used to say "Invalid email or password" — the
    verify-your-email message was unreachable, because Django refuses to
    authenticate an inactive (unverified) account before that check runs.
    """
    response = _login(api_client, unverified_user.email, PASSWORD)

    assert response.status_code == 400
    assert "verify your email" in response.data["non_field_errors"][0].lower()


def test_unverified_account_with_wrong_password_reveals_nothing(api_client, unverified_user):
    response = _login(api_client, unverified_user.email, "not-the-password")

    assert response.status_code == 400
    assert response.data["non_field_errors"] == ["Invalid email or password."]


def test_unknown_email_gets_the_same_generic_message(api_client):
    response = _login(api_client, "nobody@dut4life.ac.za", PASSWORD)

    assert response.status_code == 400
    assert response.data["non_field_errors"] == ["Invalid email or password."]

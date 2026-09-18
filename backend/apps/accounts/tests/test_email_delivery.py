import pytest
from django.core import mail

from apps.accounts.tasks import send_email, send_email_task

pytestmark = pytest.mark.django_db


def test_send_email_task_sends_from_the_configured_address(settings):
    settings.DEFAULT_FROM_EMAIL = "smartspend@example.test"

    send_email_task("Hello", "Body text", "student@dut4life.ac.za")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].from_email == "smartspend@example.test"
    assert mail.outbox[0].to == ["student@dut4life.ac.za"]
    assert mail.outbox[0].subject == "Hello"


def test_send_email_falls_back_to_inline_when_the_broker_is_unreachable(monkeypatch):
    """Regression guard: with no Celery broker reachable (local dev without
    Redis), `.delay()` raises — the email must still be sent, not dropped.
    """

    def broker_down(*args, **kwargs):
        raise ConnectionError("no broker reachable")

    monkeypatch.setattr("apps.accounts.tasks.send_email_task.delay", broker_down)

    send_email("Verify", "Link", "student@dut4life.ac.za")

    assert len(mail.outbox) == 1
    assert mail.outbox[0].subject == "Verify"


def test_registration_emails_are_delivered_through_the_task(api_client):
    response = api_client.post(
        "/api/v1/auth/register/",
        {
            "full_name": "Nomvula Khumalo",
            "email": "nomvula@dut4life.ac.za",
            "password": "Correct-Horse-9!",
            "campus": "ML Sultan",
            "popia_consent": True,
        },
        format="json",
    )

    assert response.status_code == 201
    assert len(mail.outbox) == 1
    assert "verify-email?token=" in mail.outbox[0].body

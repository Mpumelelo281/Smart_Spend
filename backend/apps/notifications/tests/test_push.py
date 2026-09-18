import pytest
from pywebpush import WebPushException

from apps.notifications.models import Notification, PushSubscription
from apps.notifications.push import send_web_push

pytestmark = pytest.mark.django_db


def _subscribe(client, endpoint="https://push.example/abc123"):
    return client.post(
        "/api/v1/notifications/push-subscriptions/",
        {"endpoint": endpoint, "p256dh": "p256dh-key", "auth": "auth-key"},
        format="json",
    )


def test_vapid_public_key_endpoint(authenticated_client, settings):
    settings.VAPID_PUBLIC_KEY = "test-public-key"
    response = authenticated_client.get("/api/v1/notifications/vapid-public-key/")
    assert response.status_code == 200
    assert response.data["vapid_public_key"] == "test-public-key"


def test_subscribe_creates_a_subscription(authenticated_client, student_user):
    response = _subscribe(authenticated_client)
    assert response.status_code == 201
    assert PushSubscription.objects.filter(profile=student_user.student_profile).count() == 1


def test_resubscribing_same_endpoint_updates_keys_instead_of_duplicating(authenticated_client, student_user):
    _subscribe(authenticated_client)
    response = authenticated_client.post(
        "/api/v1/notifications/push-subscriptions/",
        {"endpoint": "https://push.example/abc123", "p256dh": "new-key", "auth": "new-auth"},
        format="json",
    )
    assert response.status_code == 201
    subscriptions = PushSubscription.objects.filter(profile=student_user.student_profile)
    assert subscriptions.count() == 1
    assert subscriptions.first().p256dh == "new-key"


def test_unsubscribe_removes_the_subscription(authenticated_client, student_user):
    _subscribe(authenticated_client)
    response = authenticated_client.post(
        "/api/v1/notifications/push-subscriptions/unsubscribe/",
        {"endpoint": "https://push.example/abc123"},
        format="json",
    )
    assert response.status_code == 204
    assert not PushSubscription.objects.filter(profile=student_user.student_profile).exists()


def test_unsubscribe_requires_endpoint(authenticated_client):
    response = authenticated_client.post(
        "/api/v1/notifications/push-subscriptions/unsubscribe/", {}, format="json"
    )
    assert response.status_code == 400


def test_send_web_push_skips_when_not_configured(student_user):
    notification = Notification.objects.create(
        profile=student_user.student_profile,
        notif_type=Notification.NotifType.SYSTEM,
        message="Hello",
        channel=Notification.Channel.PUSH,
    )
    send_web_push(notification.notification_id)  # no VAPID keys in tests — must not raise


def test_send_web_push_delivers_to_every_subscription(settings, student_user, monkeypatch):
    settings.VAPID_PUBLIC_KEY = "test-public-key"
    settings.VAPID_PRIVATE_KEY = "test-private-key"

    profile = student_user.student_profile
    PushSubscription.objects.create(profile=profile, endpoint="https://push.example/1", p256dh="a", auth="b")
    PushSubscription.objects.create(profile=profile, endpoint="https://push.example/2", p256dh="c", auth="d")
    notification = Notification.objects.create(
        profile=profile,
        notif_type=Notification.NotifType.SYSTEM,
        message="Hi",
        channel=Notification.Channel.PUSH,
    )

    calls = []
    monkeypatch.setattr("apps.notifications.push.webpush", lambda **kwargs: calls.append(kwargs))

    send_web_push(notification.notification_id)
    assert len(calls) == 2


def test_send_web_push_removes_expired_subscription(settings, student_user, monkeypatch):
    settings.VAPID_PUBLIC_KEY = "test-public-key"
    settings.VAPID_PRIVATE_KEY = "test-private-key"

    profile = student_user.student_profile
    PushSubscription.objects.create(
        profile=profile, endpoint="https://push.example/dead", p256dh="a", auth="b"
    )
    notification = Notification.objects.create(
        profile=profile,
        notif_type=Notification.NotifType.SYSTEM,
        message="Hi",
        channel=Notification.Channel.PUSH,
    )

    class _Response:
        status_code = 410

    def boom(**kwargs):
        raise WebPushException("gone", response=_Response())

    monkeypatch.setattr("apps.notifications.push.webpush", boom)

    send_web_push(notification.notification_id)
    assert not PushSubscription.objects.filter(profile=profile).exists()


def test_push_subscriptions_require_authentication(api_client):
    response = api_client.post("/api/v1/notifications/push-subscriptions/", {}, format="json")
    assert response.status_code == 401

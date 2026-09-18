"""apps/notifications had no tests/ directory despite being a live,
reachable API — these exercise the endpoints directly (list, mark-one-read,
mark-all-read, RBAC and isolation between students), independent of the
budget-threshold flow already covered by apps/budgets/tests/test_notifications.py.
"""

import pytest

from apps.accounts.models import StudentProfile, User
from apps.notifications.models import Notification

pytestmark = pytest.mark.django_db


@pytest.fixture
def other_student():
    user = User.objects.create_user(email="lindiwe@dut4life.ac.za", password="Correct-Horse-9!")
    user.email_verified = True
    user.status = User.Status.ACTIVE
    user.save()
    StudentProfile.objects.create(user=user, campus="City", disbursement_day=1)
    return user


def _make_notification(profile, message="Test alert", notif_type=Notification.NotifType.SYSTEM):
    return Notification.objects.create(
        profile=profile, notif_type=notif_type, message=message, channel=Notification.Channel.PUSH
    )


def test_list_returns_only_own_notifications(authenticated_client, student_user, other_student):
    _make_notification(student_user.student_profile, "Mine")
    _make_notification(other_student.student_profile, "Not mine")

    response = authenticated_client.get("/api/v1/notifications/")
    assert response.status_code == 200
    messages = [n["message"] for n in response.data]
    assert messages == ["Mine"]


def test_list_is_capped_and_ordered_newest_first(authenticated_client, student_user):
    first = _make_notification(student_user.student_profile, "First")
    second = _make_notification(student_user.student_profile, "Second")

    response = authenticated_client.get("/api/v1/notifications/")
    ids = [n["notification_id"] for n in response.data]
    assert ids == [str(second.notification_id), str(first.notification_id)]


def test_mark_read_rejects_another_students_notification(authenticated_client, other_student):
    notification = _make_notification(other_student.student_profile)

    response = authenticated_client.post(f"/api/v1/notifications/{notification.notification_id}/read/")
    assert response.status_code == 404
    notification.refresh_from_db()
    assert notification.is_read is False


def test_mark_all_read_only_touches_own_notifications(authenticated_client, student_user, other_student):
    mine = _make_notification(student_user.student_profile)
    theirs = _make_notification(other_student.student_profile)

    response = authenticated_client.post("/api/v1/notifications/mark-all-read/")
    assert response.status_code == 204

    mine.refresh_from_db()
    theirs.refresh_from_db()
    assert mine.is_read is True
    assert theirs.is_read is False


def test_mark_all_read_is_idempotent(authenticated_client, student_user):
    _make_notification(student_user.student_profile)

    first = authenticated_client.post("/api/v1/notifications/mark-all-read/")
    second = authenticated_client.post("/api/v1/notifications/mark-all-read/")
    assert first.status_code == 204
    assert second.status_code == 204


def test_mark_read_requires_authentication(api_client, student_user):
    notification = _make_notification(student_user.student_profile)
    response = api_client.post(f"/api/v1/notifications/{notification.notification_id}/read/")
    assert response.status_code == 401

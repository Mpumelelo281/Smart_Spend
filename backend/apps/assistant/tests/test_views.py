import pytest

pytestmark = pytest.mark.django_db


def test_requires_authentication(api_client):
    response = api_client.post("/api/v1/assistant/ask/", {"message": "Hi"}, format="json")
    assert response.status_code == 401


def test_returns_a_reply_for_an_authenticated_student(authenticated_client):
    response = authenticated_client.post("/api/v1/assistant/ask/", {"message": "Hi"}, format="json")
    assert response.status_code == 200
    assert "SpendWise" in response.data["reply"]
    assert response.data["intent"] == "greeting"
    assert response.data["quick_replies"]


def test_rejects_blank_message(authenticated_client):
    response = authenticated_client.post("/api/v1/assistant/ask/", {"message": "   "}, format="json")
    assert response.status_code == 400


def test_scoped_to_the_asking_students_own_data(authenticated_client, student_user):
    """Regression guard for Rule 9: a student's chat answer must only ever
    reflect their own StudentProfile, never be swayed by another
    student's budget rows existing in the same table."""
    from apps.accounts.models import StudentProfile, User
    from apps.budgets.models import Budget

    other = User.objects.create_user(email="other@dut4life.ac.za", password="Correct-Horse-9!")
    other_profile = StudentProfile.objects.create(user=other, campus="ML Sultan")
    Budget.objects.create(profile=other_profile, month=1, year=2020, total_allocated="9999.00")

    response = authenticated_client.post(
        "/api/v1/assistant/ask/", {"message": "How much budget do I have left?"}, format="json"
    )
    assert response.status_code == 200
    assert "don't have a budget" in response.data["reply"]

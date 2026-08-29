import pytest
from rest_framework.test import APIClient

from apps.accounts.models import StudentProfile, User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(email="thabo@dut4life.ac.za", password="Correct-Horse-9!")
    user.email_verified = True
    user.status = User.Status.ACTIVE
    user.save()
    StudentProfile.objects.create(user=user, campus="Steve Biko", disbursement_day=1)
    return user


@pytest.fixture
def authenticated_client(api_client, student_user):
    from rest_framework_simplejwt.tokens import RefreshToken

    token = RefreshToken.for_user(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {token.access_token}")
    return api_client

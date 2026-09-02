import pytest
from django.core.cache import cache
from rest_framework.test import APIClient

from apps.accounts.models import StudentProfile, User


@pytest.fixture(autouse=True)
def _isolate_from_local_dev_env(settings):
    """The test suite must never depend on whatever a developer happens to
    have in their own local .env:
      - testing escape hatches (see .env.example) left on would silently
        stop the suite from testing the real rule at all;
      - a real SERPAPI_KEY would make ordinary search tests fire genuine
        network requests against SerpApi, burning real quota and making
        results non-deterministic. Tests that specifically exercise the
        live adapter set settings.SERPAPI_KEY themselves within the test
        (see test_serpapi_adapter.py, test_live_search.py) and mock the
        actual HTTP call — that override applies on top of this default.
    """
    settings.ENFORCE_EMAIL_DOMAIN_RESTRICTION = True
    settings.SKIP_AUTH_VERIFICATION_FOR_TESTING = False
    settings.SERPAPI_KEY = ""


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    """Django's per-test DB rollback does not touch the cache — without
    this, ScopedRateThrottle's request counts (and live_search.py's
    15-minute dedupe guard) leak between unrelated tests sharing one
    process, so an early test can trip a later, otherwise-unrelated
    test's rate limit.
    """
    cache.clear()
    yield
    cache.clear()


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

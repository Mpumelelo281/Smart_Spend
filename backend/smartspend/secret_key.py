"""Refuse to run in production with the placeholder SECRET_KEY.

settings.py falls back to INSECURE_DEFAULT so a fresh local checkout boots
with no configuration. That value is public (it's in the repo), so a
deployed instance that silently fell back to it would let anyone forge JWTs
and session cookies. Render, for one, skips any `sync: false` variable that
was left blank in the Blueprint form — the variable simply never exists —
so "forgot to set it" has to fail loudly at startup, not quietly succeed.
"""

from django.core.exceptions import ImproperlyConfigured

INSECURE_DEFAULT = "insecure-dev-key-change-me"


def require_real_secret_key(secret_key: str, debug: bool) -> str:
    if not debug and secret_key == INSECURE_DEFAULT:
        raise ImproperlyConfigured(
            "DJANGO_SECRET_KEY is not set, and DEBUG is off. Refusing to start with the placeholder "
            "key from the repo. Set DJANGO_SECRET_KEY to a long random value (e.g. "
            "python -c \"import secrets; print(secrets.token_urlsafe(50))\")."
        )
    return secret_key

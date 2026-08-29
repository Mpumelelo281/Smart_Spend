"""Short-lived signed tokens used only to bridge the two steps of MFA login
(password verified -> TOTP verified) and MFA enrolment, so the client never
has to resend the password for step 2 and a bearer JWT is never issued
before both factors have checked out.
"""

from django.conf import settings
from django.core import signing

_SALT_LOGIN = "accounts.mfa.login"
_SALT_SETUP = "accounts.mfa.setup"


def issue_login_challenge(user_id) -> str:
    return signing.dumps({"user_id": str(user_id)}, salt=_SALT_LOGIN)


def read_login_challenge(token: str) -> str:
    data = signing.loads(token, salt=_SALT_LOGIN, max_age=settings.PRE_AUTH_TOKEN_MAX_AGE_SECONDS)
    return data["user_id"]


def issue_setup_challenge(user_id, secret: str) -> str:
    return signing.dumps({"user_id": str(user_id), "secret": secret}, salt=_SALT_SETUP)


def read_setup_challenge(token: str) -> dict:
    return signing.loads(token, salt=_SALT_SETUP, max_age=settings.PRE_AUTH_TOKEN_MAX_AGE_SECONDS)

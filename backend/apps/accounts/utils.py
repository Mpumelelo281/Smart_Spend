"""TOTP MFA helpers and DUT-email-domain verification helpers.

FR/NFR: "TOTP multi-factor authentication"; registration requires "DUT
email verification".
"""

import uuid

import pyotp
from django.conf import settings
from django.core.exceptions import ValidationError


def is_allowed_student_email(email: str) -> bool:
    domain = email.rsplit("@", 1)[-1].lower()
    return domain in {d.lower() for d in settings.EMAIL_VERIFICATION_ALLOWED_DOMAINS}


def validate_dut_email(email: str) -> None:
    # ENFORCE_EMAIL_DOMAIN_RESTRICTION is a local/testing escape hatch only
    # (see .env.example) — it must never be False in a deployed
    # environment, since the DUT-domain gate is the actual FR, not a dev
    # convenience. Defaults to True everywhere.
    if not settings.ENFORCE_EMAIL_DOMAIN_RESTRICTION:
        return
    if not is_allowed_student_email(email):
        allowed = ", ".join(settings.EMAIL_VERIFICATION_ALLOWED_DOMAINS)
        raise ValidationError(f"Registration requires a DUT email address ({allowed}).")


def generate_mfa_secret() -> str:
    return pyotp.random_base32()


def provisioning_uri(email: str, secret: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(name=email, issuer_name=settings.MFA_ISSUER_NAME)


def verify_totp_code(secret: str, code: str) -> bool:
    if not secret or not code:
        return False
    return pyotp.TOTP(secret).verify(code, valid_window=1)


def new_verification_token() -> uuid.UUID:
    return uuid.uuid4()

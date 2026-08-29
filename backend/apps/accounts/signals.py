"""Covers the Django-admin login path (django.contrib.auth session login)
with the same audit log the DRF/JWT views write to explicitly — see
views.py for the API login path, which calls `audit.log_action` directly
because SimpleJWT does not fire `user_logged_in` on its own.
"""

from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.dispatch import receiver

from .audit import log_action


@receiver(user_logged_in)
def on_login(sender, request, user, **kwargs):
    log_action("LOGIN_SUCCESS", actor=user)


@receiver(user_logged_out)
def on_logout(sender, request, user, **kwargs):
    log_action("LOGOUT", actor=user)


@receiver(user_login_failed)
def on_login_failed(sender, credentials, request=None, **kwargs):
    email = credentials.get("email", credentials.get("username", ""))
    log_action("LOGIN_FAILED", actor=None, metadata={"email": email})

"""Outbound email (verification, password reset), sent from a Celery worker.

Why not inline in the request: Render blocks outbound SMTP ports 25/465/587
on *free* web services, and Gmail SMTP only offers 465/587 — so the free
API instance can't reach Gmail at all. The Celery worker is a paid
instance, which isn't restricted, so it sends the mail instead. It also
keeps a slow mail server from holding up a registration request.

`send_email` falls back to sending inline if the task can't be enqueued
(e.g. local dev with no Redis/worker running) — same reasoning as
budgets.TransactionSerializer: a verification email that silently never
sends is worse than one that's occasionally not async.
"""

import logging

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


# smtplib.SMTPException subclasses OSError, so this retries transient
# mail-server/network failures a few times with backoff, but not bugs.
@shared_task(
    name="accounts.send_email",
    autoretry_for=(OSError,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def send_email_task(subject: str, message: str, recipient: str) -> None:
    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[recipient],
    )


def send_email(subject: str, message: str, recipient: str) -> None:
    try:
        send_email_task.delay(subject, message, recipient)
    except Exception:  # pylint: disable=broad-except
        logger.warning("Could not enqueue email (no Celery broker reachable?) — sending inline instead.")
        send_email_task(subject, message, recipient)

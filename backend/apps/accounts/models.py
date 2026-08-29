"""
Entities: User, StudentProfile (per the ERD — 2 of the 11).

AuditLog is additional infrastructure required by Rule 8 (append-only audit
log for every administrative action and authentication event); it is not
one of the 11 domain entities but has to live somewhere, and auth events are
its single largest source, so it lives in this app.

A note on `password` vs the ERD's `password_hash`: Django's AbstractBaseUser
hard-codes the attribute name `password` throughout `django.contrib.auth`
(set_password/check_password, the admin's password-change view, every auth
backend). Renaming that field would mean re-implementing large parts of
Django's auth machinery by hand for no behavioural benefit — the column
*is* a salted hash either way. We keep Django's `password` field and do not
duplicate it under a second name; this is the one deliberate, documented
deviation from the spec's literal field list.
"""

import uuid

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from .managers import UserManager


class User(AbstractBaseUser, PermissionsMixin):
    class Role(models.TextChoices):
        STUDENT = "STUDENT", "Student"
        ADMINISTRATOR = "ADMINISTRATOR", "Administrator"
        STUDENT_SERVICES = "STUDENT_SERVICES", "Student Services Officer"

    class Status(models.TextChoices):
        PENDING_VERIFICATION = "PENDING_VERIFICATION", "Pending email verification"
        ACTIVE = "ACTIVE", "Active"
        SUSPENDED = "SUSPENDED", "Suspended"

    user_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STUDENT)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.PENDING_VERIFICATION)

    # --- framework-required flags, kept separate from `status`/`role` so
    # Django's own auth/admin machinery has the booleans it expects ---
    is_staff = models.BooleanField(default=False)

    # --- MFA (NFR Security: TOTP multi-factor authentication) ---
    mfa_secret = models.CharField(max_length=64, blank=True)
    mfa_enabled = models.BooleanField(default=False)

    # --- DUT email verification ---
    email_verified = models.BooleanField(default=False)
    email_verification_token = models.UUIDField(default=uuid.uuid4, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        db_table = "user"
        indexes = [models.Index(fields=["role"]), models.Index(fields=["status"])]

    def __str__(self):
        return self.email

    @property
    def is_active(self):
        # Derived from `status` instead of a duplicate boolean, so there is
        # exactly one source of truth for "can this account authenticate".
        return self.status == self.Status.ACTIVE

    @is_active.setter
    def is_active(self, value):
        # Django's createsuperuser / some auth internals assign this.
        self.status = self.Status.ACTIVE if value else self.Status.SUSPENDED


class StudentProfile(models.Model):
    """FR: one-to-one with User. Financial/PII data lives here, deliberately
    split from `User`, so it can be erased on a POPIA subject-access/erasure
    request while the authentication record (and its audit trail) survives.
    """

    profile_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="student_profile")

    allowance_amount = models.DecimalField(max_digits=8, decimal_places=2, default="1650.00")
    disbursement_day = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(31)], default=1
    )
    campus = models.CharField(max_length=120)
    residence = models.CharField(max_length=120, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "student_profile"
        constraints = [
            models.CheckConstraint(
                check=models.Q(allowance_amount__gte=0), name="student_profile_allowance_non_negative"
            )
        ]

    def __str__(self):
        return f"Profile<{self.user.email}>"


class AuditLog(models.Model):
    """Append-only. No view/admin registers update or delete for this model —
    see Rule 8: "No administrative code path may complete without one."
    """

    audit_id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="audit_entries"
    )
    action = models.CharField(max_length=100)
    target_type = models.CharField(max_length=100, blank=True)
    target_id = models.CharField(max_length=64, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "audit_log"
        indexes = [
            models.Index(fields=["action"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.action} by {self.actor_id} @ {self.created_at:%Y-%m-%d %H:%M:%S}"

    def save(self, *args, **kwargs):
        if self.pk and AuditLog.objects.filter(pk=self.pk).exists():
            raise RuntimeError("AuditLog is append-only: existing entries cannot be modified.")
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise RuntimeError("AuditLog is append-only: entries cannot be deleted.")

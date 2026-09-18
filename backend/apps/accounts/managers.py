from django.contrib.auth.base_user import BaseUserManager


class UserManager(BaseUserManager):
    """Email is the login identifier — SmartSpend has no username field."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address.")
        # normalize_email only lowercases the *domain*. RegisterSerializer
        # and LoginSerializer both lowercase the whole address, so an
        # account created any other way (createsuperuser, the admin, a
        # shell) with a capital in the local part would be stored as-is
        # and then never match the lowercased lookup at login.
        email = self.normalize_email(email).lower()
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", self.model.Role.STUDENT)
        extra_fields.setdefault("status", self.model.Status.PENDING_VERIFICATION)
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("role", self.model.Role.ADMINISTRATOR)
        extra_fields.setdefault("status", self.model.Status.ACTIVE)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("email_verified", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self._create_user(email, password, **extra_fields)

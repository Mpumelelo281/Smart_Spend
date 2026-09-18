"""
Django settings for SmartSpend.

Configuration is read from environment variables only (never hard-coded),
per the project's non-negotiable rule: "Keep configuration in environment
variables, never in code."
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="insecure-dev-key-change-me")
DEBUG = env("DEBUG")
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])

# ---------------------------------------------------------------------------
# Applications
# ---------------------------------------------------------------------------
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_celery_beat",
]

LOCAL_APPS = [
    "apps.accounts",
    "apps.budgets",
    "apps.catalog",
    "apps.recommendations",
    "apps.notifications",
    "apps.reporting",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    # Serves STATIC_ROOT directly from the app process — the admin's own
    # CSS/JS, mainly. No CDN/object storage needed for a project this
    # size; whitenoise is the standard, zero-extra-infra way to do this
    # on a single-dyno-style host like Render.
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # FR8/FR9 support: attaches request.audit_context (ip, user) so any
    # view/signal that writes an AuditLog entry can record who did what from
    # where, without every view having to thread the request through by hand.
    "apps.accounts.middleware.AuditContextMiddleware",
]

ROOT_URLCONF = "smartspend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "smartspend.wsgi.application"
ASGI_APPLICATION = "smartspend.asgi.application"

# ---------------------------------------------------------------------------
# Database — PostgreSQL 16. JSONB and full-text search require Postgres;
# there is deliberately no SQLite fallback for dev/test so behaviour never
# diverges from production (see docker-compose.yml `db` service).
# ---------------------------------------------------------------------------
_DEFAULT_DB_URL = "postgres://smartspend:smartspend@localhost:5432/smartspend"
_DEFAULT_REPORTING_DB_URL = "postgres://smartspend_reporting:smartspend_reporting@localhost:5432/smartspend"

DATABASES = {
    "default": env.db("DATABASE_URL", default=_DEFAULT_DB_URL),
    # Read-only reporting role restricted (at the DB grant level — see
    # infra/sql/001_init_roles.sql) to the anonymised materialised views
    # used by Student Services Officer reports. Enforcing this as a
    # *separate DB role*, not just a Django permission, means a bug in
    # application code cannot leak row-level student data through the
    # reporting connection even if RBAC checks are somehow bypassed.
    "reporting": env.db("REPORTING_DATABASE_URL", default=_DEFAULT_REPORTING_DB_URL),
}
DATABASE_ROUTERS = ["smartspend.db_router.ReportingRouter"]

# ---------------------------------------------------------------------------
# Password hashing — FR/NFR Security: "bcrypt at work factor 12".
# BCryptSHA256PasswordHasher.rounds defaults to 12; listed first so it is
# used for all newly-set passwords. Other hashers are kept only so existing
# hashes of other formats can still be verified/upgraded, never used to
# create new hashes.
# ---------------------------------------------------------------------------
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.BCryptSHA256PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# ---------------------------------------------------------------------------
# DRF / JWT
# ---------------------------------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    # NFR: paginate search/report results at 20 per page.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.ScopedRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        # NFR Security: rate limiting on authentication endpoints.
        "auth": "10/min",
        "mfa": "10/min",
    },
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    # User's PK is `user_id`, not Django's default `id` — see accounts.User.
    "USER_ID_FIELD": "user_id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:5173"])

# ---------------------------------------------------------------------------
# Celery / Redis — background jobs (price refresh, notification dispatch)
# and the 15-minute price cache both live on the same Redis instance,
# separated by logical DB index.
# ---------------------------------------------------------------------------
REDIS_URL = env("REDIS_URL", default="redis://localhost:6379/0")
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default=REDIS_URL)
CELERY_RESULT_BACKEND = env("CELERY_RESULT_BACKEND", default=REDIS_URL)
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "Africa/Johannesburg"
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
# Local-testing-only escape hatch (parallel to CACHE_BACKEND=locmem above):
# runs every Celery task inline, synchronously, with no broker at all.
# Never set outside a developer's own machine or the test suite (see
# conftest.py) — real dev/docker/production always run an actual worker.
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
CELERY_TASK_EAGER_PROPAGATES = CELERY_TASK_ALWAYS_EAGER

_CACHE_BACKEND = env("CACHE_BACKEND", default="redis")
if _CACHE_BACKEND == "locmem":
    # Local-dev-without-Docker escape hatch only: lets `manage.py runserver`
    # work (including the auth-endpoint throttle, which reads this cache)
    # on a machine with no Redis installed. Never set CACHE_BACKEND=locmem
    # in docker-compose or production — Rule 4's 15-minute price cache and
    # the auth throttle must be the shared, process-independent Redis
    # instance there, not a per-process in-memory dict.
    CACHES = {"default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache"}}
else:
    CACHES = {
        "default": {
            "BACKEND": "django_redis.cache.RedisCache",
            "LOCATION": env("PRICE_CACHE_URL", default="redis://localhost:6379/1"),
            "OPTIONS": {"CLIENT_CLASS": "django_redis.client.DefaultClient"},
        }
    }
# FR4: price search results are cached for exactly 15 minutes.
PRICE_CACHE_TTL_SECONDS = 900

# ---------------------------------------------------------------------------
# Notification / k-anonymity / MFA configuration — kept here, not hard-coded
# in business logic, so they can be tuned per deployment without a code
# change.
# ---------------------------------------------------------------------------
BUDGET_ALERT_THRESHOLD_PCT = env.int("BUDGET_ALERT_THRESHOLD_PCT", default=80)
K_ANONYMITY_THRESHOLD = env.int("K_ANONYMITY_THRESHOLD", default=10)
MFA_ISSUER_NAME = env("MFA_ISSUER_NAME", default="SmartSpend")
EMAIL_VERIFICATION_ALLOWED_DOMAINS = env.list(
    "EMAIL_VERIFICATION_ALLOWED_DOMAINS", default=["dut4life.ac.za", "dut.ac.za"]
)
# Testing-only escape hatch — see apps/accounts/utils.py::validate_dut_email.
# Defaults True (rule enforced) everywhere; only ever set False in a local
# .env, never in docker-compose or a deployed environment.
ENFORCE_EMAIL_DOMAIN_RESTRICTION = env.bool("ENFORCE_EMAIL_DOMAIN_RESTRICTION", default=True)

# Testing-only escape hatch — see RegisterView/LoginView in
# apps/accounts/views.py. Auto-verifies email on registration and skips
# the TOTP MFA step on login entirely. Defaults False (both controls
# enforced) everywhere; only ever set True in a local .env.
SKIP_AUTH_VERIFICATION_FOR_TESTING = env.bool("SKIP_AUTH_VERIFICATION_FOR_TESTING", default=False)

# apps/catalog/adapters/serpapi_google_shopping.py — live product search.
# Blank by default: SerpApiGoogleShoppingAdapter.is_configured() returns
# False and live_search.py silently skips it, so the app still works
# (against seeded/previously-fetched data) with no key set at all.
SERPAPI_KEY = env("SERPAPI_KEY", default="")
SERPAPI_GOOGLE_DOMAIN = env("SERPAPI_GOOGLE_DOMAIN", default="google.co.za")
SERPAPI_COUNTRY = env("SERPAPI_COUNTRY", default="za")

# apps/catalog/adapters/{checkers,shoprite,mr_price}.py — each stays inert
# (is_configured() False, silently skipped by live_search.py) until its
# base URL is set. Blank by default, same as SERPAPI_KEY: see each
# adapter's docstring on verifying the endpoint before ever configuring
# these in a deployed environment.
CHECKERS_API_BASE_URL = env("CHECKERS_API_BASE_URL", default="")
CHECKERS_API_KEY = env("CHECKERS_API_KEY", default="")
SHOPRITE_API_BASE_URL = env("SHOPRITE_API_BASE_URL", default="")
SHOPRITE_API_KEY = env("SHOPRITE_API_KEY", default="")
MR_PRICE_API_BASE_URL = env("MR_PRICE_API_BASE_URL", default="")
MR_PRICE_API_KEY = env("MR_PRICE_API_KEY", default="")

# Web Push (apps/notifications/push.py) — Notification.Channel.PUSH
# delivery. Generate a keypair with `vapid --gen` (from the py-vapid
# package, a pywebpush dependency) or `openssl ecparam -genkey -name
# prime256v1`. Blank by default: send_web_push logs and returns instead of
# sending when either key is missing, so the app still works with no VAPID
# keys configured, just without push delivery (in-app/email notifications
# are unaffected).
VAPID_PUBLIC_KEY = env("VAPID_PUBLIC_KEY", default="")
VAPID_PRIVATE_KEY = env("VAPID_PRIVATE_KEY", default="")
VAPID_ADMIN_EMAIL = env("VAPID_ADMIN_EMAIL", default="no-reply@smartspend.dut4life.ac.za")

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
]

# ---------------------------------------------------------------------------
# Internationalisation
# ---------------------------------------------------------------------------
LANGUAGE_CODE = "en-za"
TIME_ZONE = "Africa/Johannesburg"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    # Content-hashed filenames + gzip/brotli precompression, served
    # straight out of collectstatic's output by WhiteNoiseMiddleware above.
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"},
}

# ---------------------------------------------------------------------------
# Outbound email — DUT email verification links, budget-threshold alerts.
# Defaults to the console backend so a fresh dev checkout never accidentally
# sends real mail; docker-compose / production set EMAIL_BACKEND to SMTP.
# ---------------------------------------------------------------------------
EMAIL_BACKEND = env("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=True)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="no-reply@smartspend.dut4life.ac.za")
FRONTEND_BASE_URL = env("FRONTEND_BASE_URL", default="http://localhost:5173")

# Pre-auth tokens issued between "password verified" and "TOTP verified"
# during the two-step MFA login (see apps/accounts/tokens.py).
PRE_AUTH_TOKEN_MAX_AGE_SECONDS = env.int("PRE_AUTH_TOKEN_MAX_AGE_SECONDS", default=300)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ---------------------------------------------------------------------------
# Transport security (NFR: TLS 1.3 terminated at the Azure App Service /
# reverse-proxy layer; these settings harden the Django side of that link).
# ---------------------------------------------------------------------------
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = not DEBUG
CSRF_COOKIE_SECURE = not DEBUG
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=not DEBUG)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": env("DJANGO_LOG_LEVEL", default="INFO")},
}

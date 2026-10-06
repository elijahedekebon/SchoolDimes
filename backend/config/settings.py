"""
Django settings for the SchoolDimes backend (Part 1 foundation).
"""

from datetime import timedelta
from pathlib import Path

import environ

BASE_DIR = Path(__file__).resolve().parent.parent

env = environ.Env(DEBUG=(bool, False))
environ.Env.read_env(BASE_DIR / ".env")

SECRET_KEY = env("DJANGO_SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env.bool("DEBUG", default=True)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["*"])

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third-party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "django_filters",
    "django_celery_beat",
    "corsheaders",
    # schooldimes apps
    "core",
    "accounts",
    "tenants",
    "students",
    "cards",
    "wallets",
    "content",
    # Part 2
    "notifications",
    "payments",
    "pooled_funds",
    "policies",
    "pos",
    "fees",
    "attendance",
    "merchants",
    "disputes",
    "privacy",
    "analytics",
    # Part 4A
    "backoffice",
    "parents",
    # Web surfaces (Django templates + HTMX; see docs/WEB_MIGRATION_PLAN.md)
    "web.core",
    "web.school",
    "web.platform",
    "web.student",
    "web.give",
]

AUTH_USER_MODEL = "accounts.User"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

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
                "web.core.context_processors.app_frame",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Database
# DATABASE_URL, e.g. postgres://user:pass@host:5432/dbname
DATABASES = {
    "default": env.db(
        "DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
    )
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

# Internationalization -- proposal S5: English, Luganda, Kiswahili.
LANGUAGE_CODE = "en"
TIME_ZONE = "Africa/Kampala"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("en", "English"),
    ("lg", "Luganda"),
    ("sw", "Kiswahili"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
# WhiteNoise serves /static/ from the web container (no extra service).
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"},
}
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Django REST Framework

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        # Part 4A: simplejwt + student-portal allowlist (core/authentication.py)
        "core.authentication.SchoolDimesJWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_PAGINATION_CLASS": "core.pagination.StandardResultsSetPagination",
    "PAGE_SIZE": 20,
    "DEFAULT_FILTER_BACKENDS": ["django_filters.rest_framework.DjangoFilterBackend"],
    "EXCEPTION_HANDLER": "core.exception_handler.api_exception_handler",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "SIGNING_KEY": env("JWT_SIGNING_KEY", default=SECRET_KEY),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.redis.RedisCache",
        "LOCATION": env("REDIS_URL", default="redis://localhost:6379/0"),
    }
}
# Optional override for running without Redis (e.g. CACHE_URL=locmemcache://).
if env("CACHE_URL", default=""):
    CACHES = {"default": env.cache("CACHE_URL")}

# Celery
CELERY_BROKER_URL = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_RESULT_BACKEND = env("CELERY_BROKER_URL", default="redis://localhost:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"
CELERY_TASK_ALWAYS_EAGER = env.bool("CELERY_TASK_ALWAYS_EAGER", default=False)
# Installed into django_celery_beat's DB tables by the DatabaseScheduler on start.
CELERY_BEAT_SCHEDULE = {
    "run-recurring-topups": {"task": "payments.tasks.run_recurring_topups", "schedule": 15 * 60},
    "expire-stale-deposits": {"task": "payments.tasks.expire_stale_deposits", "schedule": 60 * 60},
    "retry-pending-notifications": {
        "task": "notifications.tasks.retry_pending_notifications",
        "schedule": 10 * 60,
    },
}

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "loggers": {"schooldimes": {"handlers": ["console"], "level": "INFO"}},
}

# ---------------------------------------------------------------------------
# Part 2 business settings (all overridable from the environment; see
# backend/.env.example for what each one means).
# ---------------------------------------------------------------------------
MAX_TRANSACTION_AMOUNT = env.int("MAX_TRANSACTION_AMOUNT", default=5_000_000)

AGGREGATOR_MODE = env("AGGREGATOR_MODE", default="mock")
PAYMENT_AGGREGATOR_API_KEY = env("PAYMENT_AGGREGATOR_API_KEY", default="")
PAYMENT_AGGREGATOR_BASE_URL = env("PAYMENT_AGGREGATOR_BASE_URL", default="")
PAYMENT_AGGREGATOR_WEBHOOK_SECRET = env(
    "PAYMENT_AGGREGATOR_WEBHOOK_SECRET", default="dev-only-webhook-secret"
)
DEPOSIT_EXPIRY_HOURS = env.int("DEPOSIT_EXPIRY_HOURS", default=24)
RECURRING_TOPUP_MAX_FAILURES = env.int("RECURRING_TOPUP_MAX_FAILURES", default=3)
RECURRING_TOPUP_RUN_HOUR = env.int("RECURRING_TOPUP_RUN_HOUR", default=8)
PUBLIC_TOPUP_BASE_URL = env("PUBLIC_TOPUP_BASE_URL", default="http://localhost:8000/give")  # the /give/{token} web page
PUBLIC_TOPUP_THROTTLE_RATE = env("PUBLIC_TOPUP_THROTTLE_RATE", default="20/min")

SMS_BACKEND = env("SMS_BACKEND", default="log")
AFRICASTALKING_USERNAME = env("AFRICASTALKING_USERNAME", default="")
AFRICASTALKING_API_KEY = env("AFRICASTALKING_API_KEY", default="")
AFRICASTALKING_SENDER_ID = env("AFRICASTALKING_SENDER_ID", default="")
PUSH_BACKEND = env("PUSH_BACKEND", default="log")
FCM_PROJECT_ID = env("FCM_PROJECT_ID", default="")
FCM_SERVICE_ACCOUNT_FILE = env("FCM_SERVICE_ACCOUNT_FILE", default="")

# Low-balance alert level when neither the parent nor the school set one.
LOW_BALANCE_DEFAULT_THRESHOLD = env.int("LOW_BALANCE_DEFAULT_THRESHOLD", default=2000)
# P2P "pressure or bullying" pattern rules (Section C).
P2P_ALERT_WINDOW_DAYS = env.int("P2P_ALERT_WINDOW_DAYS", default=7)
P2P_ALERT_DISTINCT_SENDERS = env.int("P2P_ALERT_DISTINCT_SENDERS", default=4)
P2P_ALERT_NEAR_CAP_RATIO = env.float("P2P_ALERT_NEAR_CAP_RATIO", default=0.8)
P2P_ALERT_NEAR_CAP_COUNT = env.int("P2P_ALERT_NEAR_CAP_COUNT", default=3)
# At most one low-balance alert per guardian per wallet in this many hours.
LOW_BALANCE_ALERT_THROTTLE_HOURS = env.int("LOW_BALANCE_ALERT_THROTTLE_HOURS", default=12)


# ---------------------------------------------------------------------------
# Part 4A -- web surfaces
# ---------------------------------------------------------------------------
# The admin dashboard talks to the API through its own server-side proxy, so
# browsers normally never call the API cross-origin. CORS is still configured
# (from env, never hardcoded) for tools and any direct browser client.
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=["http://localhost:3000"])
CORS_ALLOW_CREDENTIALS = False
# Per-IP rate limit for credential endpoints (login, register).
AUTH_THROTTLE_RATE = env("AUTH_THROTTLE_RATE", default="10/min")


# ---------------------------------------------------------------------------
# Web surfaces (Django templates + HTMX) -- sessions for staff/student pages.
# The REST API keeps JWT; DRF does not accept the session cookie.
# ---------------------------------------------------------------------------
LOGIN_URL = "/login"
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = "Lax"
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=False)
CSRF_COOKIE_SECURE = SESSION_COOKIE_SECURE
SESSION_COOKIE_AGE = env.int("SESSION_COOKIE_AGE", default=8 * 3600)
SESSION_SAVE_EVERY_REQUEST = True  # sliding expiry: renewed on activity
# Backend address written into device-provisioning QR codes (a LAN address
# for phones on the school Wi-Fi). Blank = the address the admin browses on.
DEVICE_API_BASE_URL = env("DEVICE_API_BASE_URL", default="")

# Part 3: PBKDF2 iterations for CARD PINs (user passwords keep Django's default).
# Offline POS devices verify these on low-end phones; see DECISIONS.md.
CARD_PIN_HASH_ITERATIONS = env.int("CARD_PIN_HASH_ITERATIONS", default=40000)

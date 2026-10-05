import logging
import os
from pathlib import Path
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from django.core.exceptions import ImproperlyConfigured
from dotenv import load_dotenv

from auth.email_settings import get_email_settings, resolve_email_backend

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")
getenv = os.getenv
logger = logging.getLogger(__name__)

SECRET_KEY = (getenv("DJANGO_SECRET_KEY") or getenv("SECRET_KEY") or "").strip()
if not SECRET_KEY:
    raise ImproperlyConfigured("SECRET_KEY is required")

DEBUG = getenv("DEBUG", "False") == "True"
DEVELOPMENT_MODE = getenv("DEVELOPMENT_MODE", "False") == "True"

ALLOWED_HOSTS = [host for host in getenv("ALLOWED_HOSTS", "").split(",") if host]
CSRF_TRUSTED_ORIGINS = [origin for origin in getenv("CSRF_TRUSTED_ORIGINS", "").split(",") if origin]
CORS_ALLOWED_ORIGINS = [origin for origin in getenv("CORS_ALLOWED_ORIGINS", "").split(",") if origin]
CORS_ALLOW_CREDENTIALS = True

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "rest_framework_simplejwt",
    "corsheaders",
    "djoser",
    "social_django",
    "user",
    "access",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "corsheaders.middleware.CorsMiddleware",
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
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "user.UserAccount"
GATEWAY_INTERNAL_SHARED_SECRET = getenv("GATEWAY_INTERNAL_SHARED_SECRET", "")


def _append_search_path(options, search_path):
    existing = options.get("options", "").strip()
    token = f"-c search_path={search_path}"
    if token not in existing:
        options["options"] = f"{existing} {token}".strip()


def build_postgres_database_config():
    db_url = getenv("DATABASE_URL", "").strip()
    if db_url:
        parsed = urlparse(db_url)
        if parsed.scheme not in {"postgres", "postgresql"}:
            raise ImproperlyConfigured("DATABASE_URL must use PostgreSQL")
        query = dict(parse_qsl(parsed.query, keep_blank_values=True))
        db_name = parsed.path.lstrip("/")
        db_user = parsed.username or ""
        if db_name != db_user:
            raise ImproperlyConfigured("DB_USER == DB_NAME is required")
        options = {}
        if query.get("options"):
            options["options"] = query["options"]
        _append_search_path(options, '"Auth",public')
        return {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": db_name,
            "USER": db_user,
            "PASSWORD": parsed.password or "",
            "HOST": parsed.hostname or "",
            "PORT": str(parsed.port or "5432"),
            "OPTIONS": options,
        }

    config = {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": getenv("AUTH_DB_NAME", "Auth"),
        "USER": getenv("AUTH_DB_USER", "Auth"),
        "PASSWORD": getenv("AUTH_DB_PASSWORD", ""),
        "HOST": getenv("AUTH_DB_HOST", "localhost"),
        "PORT": getenv("AUTH_DB_PORT", "5432"),
        "OPTIONS": {},
    }
    if config.get("NAME") != config.get("USER"):
        raise ImproperlyConfigured("DB_USER == DB_NAME is required")
    _append_search_path(config["OPTIONS"], '"Auth",public')
    return config


DATABASES = {"default": build_postgres_database_config()}

AUTH_EMAIL_DEFERRED_EXTERNAL = getenv("AUTH_EMAIL_DEFERRED_EXTERNAL", "false").lower() == "true"
AUTH_EMAIL_SETTINGS = get_email_settings(
    "AUTH",
    development_mode=DEVELOPMENT_MODE,
    allow_deferred_external=AUTH_EMAIL_DEFERRED_EXTERNAL,
)
AUTH_NOTIFICATION_FROM_EMAIL = AUTH_EMAIL_SETTINGS.from_email
DEFAULT_FROM_EMAIL = AUTH_NOTIFICATION_FROM_EMAIL
SERVER_EMAIL = AUTH_NOTIFICATION_FROM_EMAIL
AWS_SES_ACCESS_KEY_ID = AUTH_EMAIL_SETTINGS.access_key_id
AWS_SES_SECRET_ACCESS_KEY = AUTH_EMAIL_SETTINGS.secret_access_key
AWS_SES_REGION_NAME = AUTH_EMAIL_SETTINGS.region_name
AWS_SES_FROM_EMAIL = AUTH_EMAIL_SETTINGS.from_email
AWS_SES_CONFIGURATION_SET = AUTH_EMAIL_SETTINGS.configuration_set
AWS_SES_RETURN_PATH = AUTH_EMAIL_SETTINGS.return_path or None
USE_SES_V2 = True
AWS_SES_REGION_ENDPOINT = f"email.{AWS_SES_REGION_NAME}.amazonaws.com" if AWS_SES_REGION_NAME else ""

EMAIL_BACKEND = resolve_email_backend(
    AUTH_EMAIL_SETTINGS,
    explicit_backend=getenv("EMAIL_BACKEND", ""),
    deferred_external=AUTH_EMAIL_DEFERRED_EXTERNAL,
)
if AUTH_EMAIL_SETTINGS.provider == "mailpit":
    EMAIL_HOST = AUTH_EMAIL_SETTINGS.smtp_host
    EMAIL_PORT = AUTH_EMAIL_SETTINGS.smtp_port
    EMAIL_USE_TLS = AUTH_EMAIL_SETTINGS.smtp_use_tls
    EMAIL_USE_SSL = False
    EMAIL_HOST_USER = getenv("AUTH_EMAIL_SMTP_USERNAME", "")
    EMAIL_HOST_PASSWORD = getenv("AUTH_EMAIL_SMTP_PASSWORD", "")
AUTH_EMAIL_DELIVERY_FAIL_OPEN = getenv("AUTH_EMAIL_DELIVERY_FAIL_OPEN", "True") == "True"

DOMAIN = getenv("DOMAIN")
SITE_NAME = getenv("SITE_NAME")
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {"min_length": 12},
    },
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
LANGUAGE_CODE = "es-MX"
TIME_ZONE = "America/Mexico_City"
USE_I18N = True
USE_TZ = True

if DEVELOPMENT_MODE is True:
    STATIC_URL = "static/"
    STATIC_ROOT = BASE_DIR / "static"
    MEDIA_URL = "media/"
    MEDIA_ROOT = BASE_DIR / "media"
else:
    AWS_S3_ACCESS_KEY_ID = getenv("AWS_S3_ACCESS_KEY_ID")
    AWS_S3_SECRET_ACCESS_KEY = getenv("AWS_S3_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = getenv("AWS_STORAGE_BUCKET_NAME")
    region_name = getenv("region_name")
    endpoint_url = f"https://${region_name}.digitaloceanspaces.com"
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=86400"}
    AWS_DEFAULT_ACL = getenv("AWS_DEFAULT_ACL")
    AWS_LOCATION = getenv("AWS_LOCATION")
    AWS_S3_CUSTOM_DOMAIN = getenv("AWS_S3_CUSTOM_DOMAIN")
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": {}},
        "staticfiles": {"BACKEND": "storages.backends.s3.S3Storage"},
    }

AUTHENTICATION_BACKENDS = [
    "social_core.backends.google.GoogleOAuth2",
    "social_core.backends.facebook.FacebookOAuth2",
    "django.contrib.auth.backends.ModelBackend",
]
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["user.authentication.CustomJWTAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
}
DJOSER = {
    "LOGIN_FIELD": "email",
    "PASSWORD_RESET_CONFIRM_URL": "password-reset/{uid}/{token}",
    "USERNAME_RESET_CONFIRM_URL": "email-reset/{uid}/{token}",
    "SEND_ACTIVATION_EMAIL": True,
    "ACTIVATION_URL": "activation/{uid}/{token}",
    "USER_CREATE_PASSWORD_RETYPE": True,
    "PASSWORD_RESET_CONFIRM_RETYPE": True,
    "TOKEN_MODEL": None,
    "SOCIAL_AUTH_ALLOWED_REDIRECT_URIS": [uri for uri in getenv("REDIRECT_URIS", "").split(",") if uri],
    "EMAIL": {
        "activation": "auth.custom_email.ActivationEmail",
        "confirmation": "auth.custom_email.ConfirmationEmail",
        "password_reset": "auth.custom_email.PasswordResetEmail",
        "password_changed_confirmation": "auth.custom_email.PasswordChangedConfirmationEmail",
        "username_reset": "auth.custom_email.UsernameResetEmail",
        "username_changed_confirmation": "auth.custom_email.UsernameChangedConfirmationEmail",
    },
}

SIMPLE_JWT = {
    "AUTH_HEADER_TYPES": ("Bearer",),
    "ACCESS_TOKEN_LIFETIME": __import__("datetime").timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": __import__("datetime").timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
}

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_KEY", "")
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv("SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET", "")
SOCIAL_AUTH_FACEBOOK_KEY = getenv("SOCIAL_AUTH_FACEBOOK_KEY", "")
SOCIAL_AUTH_FACEBOOK_SECRET = getenv("SOCIAL_AUTH_FACEBOOK_SECRET", "")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "INFO"},
}

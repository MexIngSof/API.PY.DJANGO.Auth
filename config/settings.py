import sys  # Para acceder a los argumentos de la línea de comandos
# Para parsear las URLs de bases de datos en Heroku u otros servicios
import dj_database_url
# Obtener variables de entorno y manipular rutas de archivos
from os import getenv, path
from pathlib import Path  # Para trabajar con rutas de archivos de manera más eficiente
# Para generar una clave secreta aleatoria si no se encuentra
from django.core.management.utils import get_random_secret_key
import dotenv  # Para cargar variables de entorno desde un archivo .env
from auth.email_settings import get_email_settings
from auth.cookie_policy import resolve_cookie_policy

# ===============================
# PROJECT INFO
# ===============================
PROJECT_NAME = "Auth"
DB_SCHEMA = getenv("DB_SCHEMA", PROJECT_NAME)
DB_RUNTIME_SCHEMA = getenv("AUTH_DB_RUNTIME_SCHEMA", f"{PROJECT_NAME}Runtime")

BASE_DIR = Path(__file__).resolve().parent.parent
dotenv_file = BASE_DIR/'.env.local'
if path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)

DEVELOPMENT_MODE = getenv('DEVELOPMENT_MODE', 'False') == 'True'
SECRET_KEY = getenv("DJANGO_SECRET_KEY", get_random_secret_key())
ALLOWED_HOSTS = getenv('DJANGO_ALLOWED_HOSTS',
                       '127.0.0.1,localhost,web-frontend-node,api-backend-python').split(',')

INSTALLED_APPS = [
    'django.contrib.auth', 'django.contrib.contenttypes', 'django.contrib.sessions',
    'django.contrib.staticfiles', 'corsheaders', 'rest_framework', 'djoser', 'storages',
    'social_django', 'user.apps.UserConfig', 'access', 'roles',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [{
    'BACKEND': 'django.template.backends.django.DjangoTemplates',
    'DIRS': [BASE_DIR / 'templates'],
    'APP_DIRS': True,
    'OPTIONS': {'context_processors': [
        'django.template.context_processors.debug',
        'django.template.context_processors.request',
        'django.contrib.auth.context_processors.auth',
    ]},
}]
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'


def postgres_options():
    if "test" in sys.argv:
        return getenv("AUTH_TEST_POSTGRES_OPTIONS", '-c search_path=public,"Auth","AuthRuntime"')
    return getenv("POSTGRES_OPTIONS", f'-c search_path="{DB_SCHEMA}","{DB_RUNTIME_SCHEMA}"')


def build_postgres_database_config():
    database_url = getenv('DATABASE_URL')
    if database_url:
        config = dj_database_url.parse(database_url)
        config.setdefault("OPTIONS", {})
        config["OPTIONS"]["options"] = postgres_options()
        return config
    db_name = getenv("DB_NAME") or getenv("POSTGRES_DB") or getenv("AUTH_DB_NAME") or "auth"
    db_user = getenv("DB_USER") or getenv("POSTGRES_USER") or getenv("AUTH_DB_USER") or "auth_user"
    db_password = getenv("DB_PASSWORD") or getenv("POSTGRES_PASSWORD") or getenv("AUTH_DB_PASSWORD")
    db_host = getenv("DB_HOST") or getenv("POSTGRES_HOST") or "localhost"
    db_port = getenv("DB_PORT") or getenv("POSTGRES_PORT") or "5432"
    if not db_password and len(sys.argv) > 1 and sys.argv[1] != "collectstatic":
        raise RuntimeError(
            "Auth database password is not configured. Set DB_PASSWORD, POSTGRES_PASSWORD or AUTH_DB_PASSWORD. SQLite is not allowed for Auth."
        )
    return {
        "ENGINE": getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": db_name, "USER": db_user, "PASSWORD": db_password or "",
        "HOST": db_host, "PORT": db_port,
        "OPTIONS": {"options": postgres_options()},
    }


DATABASES = {"default": build_postgres_database_config()}

AUTH_EMAIL_DEFERRED_EXTERNAL = getenv('AUTH_EMAIL_DEFERRED_EXTERNAL', 'false').lower() == 'true'
AUTH_EMAIL_SETTINGS = get_email_settings(
    "AUTH", development_mode=DEVELOPMENT_MODE, allow_deferred_external=AUTH_EMAIL_DEFERRED_EXTERNAL,
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
AWS_SES_REGION_ENDPOINT = f'email.{AWS_SES_REGION_NAME}.amazonaws.com' if AWS_SES_REGION_NAME else ''

EMAIL_BACKEND = getenv('EMAIL_BACKEND')
if not EMAIL_BACKEND:
    if AUTH_EMAIL_SETTINGS.provider == "ses" and AUTH_EMAIL_SETTINGS.is_complete:
        EMAIL_BACKEND = 'django_ses.SESBackend'
    elif AUTH_EMAIL_DEFERRED_EXTERNAL:
        EMAIL_BACKEND = 'auth.email_backends.DeferredExternalEmailBackend'
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
AUTH_EMAIL_DELIVERY_FAIL_OPEN = getenv('AUTH_EMAIL_DELIVERY_FAIL_OPEN', 'True') == 'True'

DOMAIN = getenv('DOMAIN')
SITE_NAME = getenv('SITE_NAME')
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
LANGUAGE_CODE = 'es-MX'
TIME_ZONE = 'America/Mexico_City'
USE_I18N = True
USE_TZ = True

if DEVELOPMENT_MODE is True:
    STATIC_URL = 'static/'
    STATIC_ROOT = BASE_DIR/'static'
    MEDIA_URL = 'media/'
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    AWS_S3_ACCESS_KEY_ID = getenv('AWS_S3_ACCESS_KEY_ID')
    AWS_S3_SECRET_ACCESS_KEY = getenv('AWS_S3_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = getenv('AWS_STORAGE_BUCKET_NAME')
    region_name = getenv('region_name')
    endpoint_url = f'https://${region_name}.digitaloceanspaces.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_DEFAULT_ACL = getenv('AWS_DEFAULT_ACL')
    AWS_LOCATION = getenv('AWS_LOCATION')
    AWS_S3_CUSTOM_DOMAIN = getenv('AWS_S3_CUSTOM_DOMAIN')
    STORAGES = {
        "default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": {}},
        "staticfiles": {"BACKEND": "storages.backends.s3.S3Storage"},
    }

AUTHENTICATION_BACKENDS = [
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    'django.contrib.auth.backends.ModelBackend',
]
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': ['user.authentication.CustomJWTAuthentication'],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
}
DJOSER = {
    "LOGIN_FIELD": "email",
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': True,
    'ACTIVATION_URL': 'activation/{uid}/{token}',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_RETYPE': True,
    'TOKEN_MODEL': None,
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': [uri for uri in getenv('REDIRECT_URIS', '').split(',') if uri],
    'EMAIL': {
        'activation': 'auth.custom_email.ActivationEmail',
        'confirmation': 'auth.custom_email.ConfirmationEmail',
        'password_reset': 'auth.custom_email.PasswordResetEmail',
        'password_changed_confirmation': 'auth.custom_email.PasswordChangedConfirmationEmail',
        'username_reset': 'auth.custom_email.UsernameResetEmail',
        'username_changed_confirmation': 'auth.custom_email.UsernameChangedConfirmationEmail',
    },
    "SERIALIZERS": {
        "user_create": "user.serializers.CustomUserCreatePasswordRetypeSerializer",
        "user_create_password_retype": "user.serializers.CustomUserCreatePasswordRetypeSerializer",
    },
}

# Cookie policy is derived from topology instead of being hard-coded per domain.
# Local HTTP: host-only + Secure=false + SameSite=Lax.
# HTTPS same-site dev/pro: host-only + Secure=true + SameSite=Lax.
# True cross-site: requires explicit allow-list and becomes Secure + SameSite=None.
_AUTH_COOKIE_POLICY = resolve_cookie_policy()
AUTH_COOKIE = 'access'
AUTH_COOKIE_ACCESS_MAX_AGE = 60 * 15
AUTH_COOKIE_REFRESH_MAX_AGE = 60 * 60 * 24 * 3
AUTH_COOKIE_SECURE = _AUTH_COOKIE_POLICY.secure
AUTH_COOKIE_HTTP_ONLY = True
AUTH_COOKIE_PATH = '/'
AUTH_COOKIE_SAMESITE = _AUTH_COOKIE_POLICY.same_site
AUTH_COOKIE_DOMAIN = _AUTH_COOKIE_POLICY.domain

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv('GOOGLE_AUTH_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv('GOOGLE_AUTH_SECRET_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name']
SOCIAL_AUTH_FACEBOOK_KEY = getenv('FACEBOOK_AUTH_KEY')
SOCIAL_AUTH_FACEBOOK_SECRET = getenv('FACEBOOK_AUTH_SECRET_KEY')
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {'fields': 'email, first_name, last_name'}

CORS_ALLOWED_ORIGINS = getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:3000,http://api-backend-python:3000,http://127.0.0.1:3000,http://localhost:8000,http://api-backend-python:8000,http://127.0.0.1:8000,http://localhost:8001,http://api-backend-python:8001,http://127.0.0.1:8001'
).split(',')
CORS_ALLOW_CREDENTIALS = True
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = "user.UserAccount"

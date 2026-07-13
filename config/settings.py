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

# ===============================
# PROJECT INFO
# ===============================
PROJECT_NAME = "Auth"
DB_SCHEMA = getenv("DB_SCHEMA", PROJECT_NAME)
DB_RUNTIME_SCHEMA = getenv("AUTH_DB_RUNTIME_SCHEMA", f"{PROJECT_NAME}Runtime")

# Definición de la ruta base del proyecto
BASE_DIR = Path(__file__).resolve().parent.parent

# Ruta al archivo .env local donde se encuentran las variables de entorno
dotenv_file = BASE_DIR/'.env.local'

# Si el archivo .env.local existe, cargar las variables de entorno de él
if path.isfile(dotenv_file):
    dotenv.load_dotenv(dotenv_file)  # Cargar las variables de entorno

# Determina si la aplicación está en modo de desarrollo (true o false)
DEVELOPMENT_MODE = getenv('DEVELOPMENT_MODE', 'False') == 'True'

# Configuración rápida para el modo de desarrollo, no es adecuada para producción
# Advertencia de seguridad: mantener la clave secreta en secreto
SECRET_KEY = getenv("DJANGO_SECRET_KEY", get_random_secret_key())

# Permitir solo ciertos hosts para el acceso a la app
ALLOWED_HOSTS = getenv('DJANGO_ALLOWED_HOSTS',
                       '127.0.0.1,localhost,web-frontend-node,api-backend-python').split(',')

# Definición de las aplicaciones instaladas en el proyecto
INSTALLED_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.staticfiles',
    'corsheaders',  # Para manejar solicitudes de CORS
    'rest_framework',  # Para crear APIs RESTful
    'djoser',  # Para manejar la autenticación y el registro de usuarios
    'storages',  # Para manejar almacenamiento en la nube (como AWS S3)
    'social_django',  # Para manejar la autenticación de redes sociales
    'user.apps.UserConfig',  # Aplicación personalizada de usuarios
    'access',
    'roles',
]

# Middleware para manejar la seguridad, sesiones, autenticación, etc.
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# URL de configuración raíz
ROOT_URLCONF = 'config.urls'

# Plantillas de configuración, en este caso no se está usando una carpeta e9specífica
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
            ],
        },
    },
]

# Configuración WSGI para la aplicación (usado para el despliegue)
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

def build_postgres_database_config():
    database_url = getenv('DATABASE_URL')
    if database_url:
        config = dj_database_url.parse(database_url)
        config.setdefault("OPTIONS", {})
        config["OPTIONS"]["options"] = getenv(
            "POSTGRES_OPTIONS",
            f"-c search_path=\"{DB_SCHEMA}\",\"{DB_RUNTIME_SCHEMA}\"",
        )
        return config

    db_name = getenv("DB_NAME") or getenv("POSTGRES_DB") or getenv("AUTH_DB_NAME") or "auth"
    db_user = getenv("DB_USER") or getenv("POSTGRES_USER") or getenv("AUTH_DB_USER") or "auth_user"
    db_password = getenv("DB_PASSWORD") or getenv("POSTGRES_PASSWORD") or getenv("AUTH_DB_PASSWORD")
    db_host = getenv("DB_HOST") or getenv("POSTGRES_HOST") or "localhost"
    db_port = getenv("DB_PORT") or getenv("POSTGRES_PORT") or "5432"

    if not db_password and len(sys.argv) > 1 and sys.argv[1] != "collectstatic":
        raise RuntimeError(
            "Auth database password is not configured. Set DB_PASSWORD, "
            "POSTGRES_PASSWORD or AUTH_DB_PASSWORD for local checks. "
            "SQLite is not allowed for Auth."
        )

    return {
        "ENGINE": getenv("DB_ENGINE", "django.db.backends.postgresql"),
        "NAME": db_name,
        "USER": db_user,
        "PASSWORD": db_password or "",
        "HOST": db_host,
        "PORT": db_port,
        "OPTIONS": {
            "options": getenv(
                "POSTGRES_OPTIONS",
                f"-c search_path=\"{DB_SCHEMA}\",\"{DB_RUNTIME_SCHEMA}\"",
            )
        },
    }


# Configuracion PostgreSQL unica para desarrollo y produccion. SQLite no esta permitido.
DATABASES = {
    "default": build_postgres_database_config()
}

AUTH_EMAIL_SETTINGS = get_email_settings("AUTH", development_mode=DEVELOPMENT_MODE)
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
AWS_SES_REGION_ENDPOINT = (
    f'email.{AWS_SES_REGION_NAME}.amazonaws.com'
    if AWS_SES_REGION_NAME
    else ''
)

# Configuracion de correo Auth.
# Si SES no esta completamente configurado, usar backend de consola para evitar
# registros 500 por falta de region/credenciales en ambientes locales.
EMAIL_BACKEND = getenv('EMAIL_BACKEND')
if not EMAIL_BACKEND:
    if AUTH_EMAIL_SETTINGS.provider == "ses" and AUTH_EMAIL_SETTINGS.is_complete:
        EMAIL_BACKEND = 'django_ses.SESBackend'
    else:
        EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

AUTH_EMAIL_DELIVERY_FAIL_OPEN = getenv('AUTH_EMAIL_DELIVERY_FAIL_OPEN', 'True') == 'True'

# Configuración de dominio y nombre del sitio
DOMAIN = getenv('DOMAIN')
SITE_NAME = getenv('SITE_NAME')

# Validadores de contraseñas para mejorar la seguridad
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator', },
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator', },
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator', },
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator', },
]

# Configuración de localización (idioma y zona horaria)
LANGUAGE_CODE = 'es-MX'  # Español para México
TIME_ZONE = 'America/Mexico_City'  # Zona horaria de la Ciudad de México
USE_I18N = True
USE_TZ = True

# Configuración de archivos estáticos y de medios
if DEVELOPMENT_MODE is True:
    STATIC_URL = 'static/'  # URL para archivos estáticos en desarrollo
    STATIC_ROOT = BASE_DIR/'static'  # Ruta local de los archivos estáticos
    MEDIA_URL = 'media/'  # URL para archivos multimedia
    MEDIA_ROOT = BASE_DIR / 'media'  # Ruta local de los archivos multimedia
else:
    # Configuración para usar almacenamiento en la nube en producción (AWS S3, DigitalOcean, etc.)
    AWS_S3_ACCESS_KEY_ID = getenv('AWS_S3_ACCESS_KEY_ID')
    AWS_S3_SECRET_ACCESS_KEY = getenv('AWS_S3_SECRET_ACCESS_KEY')
    AWS_STORAGE_BUCKET_NAME = getenv('AWS_STORAGE_BUCKET_NAME')
    region_name = getenv('region_name')
    endpoint_url = f'https://${region_name}.digitaloceanspaces.com'
    AWS_S3_OBJECT_PARAMETERS = {'CacheControl': 'max-age=86400'}
    AWS_DEFAULT_ACL = getenv('AWS_DEFAULT_ACL')
    AWS_LOCATION = getenv('AWS_LOCATION')
    AWS_S3_CUSTOM_DOMAIN = getenv('AWS_S3_CUSTOM_DOMAIN')

    # Configuración de almacenamiento en S3 para archivos estáticos y medios
    STORAGES = {
        "default": {
            "BACKEND": "storages.backends.s3.S3Storage",
            "OPTIONS": {},
        },
        "staticfiles": {
            "BACKEND": "storages.backends.s3.S3Storage",
        },
    }

# Configuración de autenticación
AUTHENTICATION_BACKENDS = [
    # 'social_core.backends.open_id.OpenIdAuth',
    # 'social_core.backends.google.GoogleOpenId',
    'social_core.backends.google.GoogleOAuth2',
    'social_core.backends.facebook.FacebookOAuth2',
    # 'social_core.backends.google.GoogleOAuth',
    # 'social_core.backends.twitter.TwitterOAuth',
    # 'social_core.backends.yahoo.YahooOpenId',
    # This is the default that allows us to log in via username
    # Método por defecto (usuario/contraseña)
    'django.contrib.auth.backends.ModelBackend',
    # 'account.authentication.EmailAuthBackend'
]

# Configuración del framework REST (autenticación y permisos)
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        # Autenticación personalizada con JWT
        'user.authentication.CustomJWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        # Permitir solo usuarios autenticados
        'rest_framework.permissions.IsAuthenticated',
    ]
}


# Configuracion de Djoser para la API de autenticacion
DJOSER = {
    "LOGIN_FIELD": "email",
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset/{uid}/{token}',
    'SEND_ACTIVATION_EMAIL': True,  # True
    'ACTIVATION_URL': 'activation/{uid}/{token}',
    'USER_CREATE_PASSWORD_RETYPE': True,  # True
    'PASSWORD_RESET_CONFIRM_RETYPE': True,
    'TOKEN_MODEL': None,
    'SOCIAL_AUTH_ALLOWED_REDIRECT_URIS': [
        uri for uri in getenv('REDIRECT_URIS', '').split(',') if uri
    ],

    # Rutas hacia las clases personalizadas de correo por aplicacion.
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
    }
}

# Configuracion de cookies de autenticacion
# Nombre de la cookie que almacena el token de acceso
AUTH_COOKIE = 'access'
# Duración del token de acceso en segundos (5 minutos)
# Esto es útil para seguridad, pero puede ser incómodo si no usas refresh frecuentemente.
AUTH_COOKIE_ACCESS_MAX_AGE = 60 * 15  # 300 segundos
# Duración del token de refresh en segundos (24 horas)
# Esto permite obtener nuevos tokens de acceso sin necesidad de volver a iniciar sesión
AUTH_COOKIE_REFRESH_MAX_AGE = 60 * 60 * 24 * 3  # 86400 segundos
# Indica si la cookie debe ser enviada sólo por HTTPS
# En desarrollo, podrías poner esto como False para permitir pruebas locales sin HTTPS
# getenv lee la variable de entorno 'AUTH_COOKIE_SECURE', si no está, asume 'True'
AUTH_COOKIE_SECURE = getenv('AUTH_COOKIE_SECURE', 'False') == 'True'
# Indica que la cookie no puede ser accedida por JavaScript (por seguridad)
# Muy recomendable mantenerlo en True para evitar XSS
AUTH_COOKIE_HTTP_ONLY = True
# Define la ruta desde donde la cookie será válida
# '/' significa que estará disponible para toda la app
AUTH_COOKIE_PATH = '/'
# Política SameSite, controla cómo se envían las cookies en peticiones cross-site
# 'None' permite compartir cookies entre dominios, pero **requiere** HTTPS y `secure=True`
# En producción es necesario. En desarrollo podría causarte problemas sin HTTPS.
# AUTH_COOKIE_SAMESITE = 'None'
AUTH_COOKIE_SAMESITE = getenv('AUTH_COOKIE_SAMESITE', 'Lax')


# ===============================
# AUTENTICACIÓN SOCIAL: GOOGLE Y FACEBOOK
# ===============================

# GOOGLE ===========================

# Client ID de Google OAuth 2.0, obtenido desde Google Developers Console
SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = getenv('GOOGLE_AUTH_KEY')

# Client Secret de Google OAuth 2.0
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = getenv('GOOGLE_AUTH_SECRET_KEY')

# Permisos que se solicitan al usuario durante la autenticación
# userinfo.email → para acceder al correo
# userinfo.profile → para acceder al nombre, foto de perfil, etc.
SOCIAL_AUTH_GOOGLE_OAUTH2_SCOPE = [
    'https://www.googleapis.com/auth/userinfo.email',
    'https://www.googleapis.com/auth/userinfo.profile',
]

# Campos adicionales que quieres guardar del perfil de Google
# Puedes incluir: 'first_name', 'last_name', 'email', etc.
SOCIAL_AUTH_GOOGLE_OAUTH2_EXTRA_DATA = ['first_name', 'last_name']

# FACEBOOK ===========================

# App ID de tu aplicación de Facebook
SOCIAL_AUTH_FACEBOOK_KEY = getenv('FACEBOOK_AUTH_KEY')

# App Secret de tu aplicación de Facebook
SOCIAL_AUTH_FACEBOOK_SECRET = getenv('FACEBOOK_AUTH_SECRET_KEY')

# Permisos que se solicitan al usuario durante la autenticación
# 'email' permite acceder al correo del usuario de Facebook
SOCIAL_AUTH_FACEBOOK_SCOPE = ['email']

# Campos específicos que quieres obtener del perfil de Facebook
# Esto es necesario porque por defecto Facebook no entrega toda la información
SOCIAL_AUTH_FACEBOOK_PROFILE_EXTRA_PARAMS = {
    'fields': 'email, first_name, last_name'
}


# Configuración de CORS (Cross-Origin Resource Sharing)
CORS_ALLOWED_ORIGINS = getenv(
    'CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://api-backend-python:3000,http://127.0.0.1:3000,http://localhost:8000,http://api-backend-python:8000,http://127.0.0.1:8000,http://localhost:8001,http://api-backend-python:8001,http://127.0.0.1:8001').split(',')
CORS_ALLOW_CREDENTIALS = True

# Configuración del campo de la clave primaria por defecto
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Modelo de usuario personalizado
AUTH_USER_MODEL = "user.UserAccount"

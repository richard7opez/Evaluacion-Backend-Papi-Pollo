"""
Django settings for config project.

Proyecto: Papi Pollo
"""

from pathlib import Path
from datetime import timedelta
import os

from dotenv import load_dotenv
from django.core.exceptions import ImproperlyConfigured


# ==========================================================
# RUTA BASE DEL PROYECTO
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

if not SECRET_KEY:
    raise ImproperlyConfigured(
        'Configura DJANGO_SECRET_KEY en .env o en el entorno.'
    )

DEBUG = os.environ.get(
    'DJANGO_DEBUG',
    'False'
).lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        'DJANGO_ALLOWED_HOSTS',
        'localhost,127.0.0.1'
    ).split(',')
    if host.strip()
]


# ==========================================================
# AUTENTICACIÓN
# ==========================================================

LOGIN_URL = 'login'
LOGIN_REDIRECT_URL = 'inicio'
LOGOUT_REDIRECT_URL = 'inicio'


# ==========================================================
# APLICACIONES
# ==========================================================

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'drf_spectacular',
    'drf_spectacular_sidecar',
    'api',

    # Aplicaciones del proyecto Papi Pollo
    'menu',
    'sucursales',
    'pedidos',
]


# ==========================================================
# MIDDLEWARE
# ==========================================================

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'config.urls'


# ==========================================================
# TEMPLATES
# ==========================================================

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',

        'DIRS': [
            BASE_DIR / 'templates',
        ],

        'APP_DIRS': True,

        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]


WSGI_APPLICATION = 'config.wsgi.application'


# ==========================================================
# BASE DE DATOS
# ==========================================================

DB_ENGINE = os.environ.get('DB_ENGINE', 'sqlite').strip().lower()

if DB_ENGINE == 'sqlite':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
elif DB_ENGINE in ('mysql', 'mariadb'):
    requeridas = ('DB_NAME', 'DB_USER', 'DB_PASSWORD')
    faltantes = [nombre for nombre in requeridas if not os.environ.get(nombre)]
    if faltantes:
        raise ImproperlyConfigured(
            'Faltan variables para MySQL/MariaDB: ' + ', '.join(faltantes)
        )
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ['DB_NAME'],
            'USER': os.environ['DB_USER'],
            'PASSWORD': os.environ['DB_PASSWORD'],
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES', default_storage_engine=INNODB",
            },
        }
    }
else:
    raise ImproperlyConfigured('DB_ENGINE debe ser sqlite, mysql o mariadb.')


# ==========================================================
# VALIDACIÓN DE CONTRASEÑAS
# ==========================================================

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# ==========================================================
# IDIOMA Y ZONA HORARIA
# ==========================================================

LANGUAGE_CODE = 'es-cl'

TIME_ZONE = 'America/Santiago'

USE_I18N = True

USE_TZ = True


# ==========================================================
# ARCHIVOS ESTÁTICOS
# CSS - JAVASCRIPT - IMÁGENES FIJAS - BOOTSTRAP
# ==========================================================

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

STATIC_ROOT = BASE_DIR / 'staticfiles'


# ==========================================================
# ARCHIVOS MULTIMEDIA
# IMÁGENES Y DOCUMENTOS SUBIDOS
# ==========================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================================
# EMAIL
# ==========================================================

EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'


# ==========================================================
# CLAVE PRIMARIA POR DEFECTO
# ==========================================================

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# API independiente de las sesiones y permisos de las vistas web.
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_RENDERER_CLASSES': ['rest_framework.renderers.JSONRenderer'],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'EXCEPTION_HANDLER': 'api.exceptions.exception_handler',
    'DEFAULT_THROTTLE_RATES': {'tokens': '10/min'},
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

JWT_SIGNING_KEY = os.environ.get('JWT_SIGNING_KEY', '')
if len(JWT_SIGNING_KEY.encode()) < 32:
    raise ImproperlyConfigured(
        'JWT_SIGNING_KEY debe tener al menos 32 bytes aleatorios. '
        'Ejecuta python -m api.configurar_clave_jwt para configurar .env.'
    )

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=5),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'SIGNING_KEY': JWT_SIGNING_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'UPDATE_LAST_LOGIN': False,
    'CHECK_REVOKE_TOKEN': True,
}

SPECTACULAR_SETTINGS = {
    'TITLE': 'Papi Pollo API',
    'DESCRIPTION': 'Evaluacion Sumativa 3. API con permisos Django y JWT. '
                   'Administrador: CRUD; Operador: consulta/alta/edicion; Consulta: lectura. '
                   'Los campos privados de Pedido y la ficha tecnica se reservan al Administrador.',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SWAGGER_UI_DIST': 'SIDECAR',
    'SWAGGER_UI_FAVICON_HREF': 'SIDECAR',
    'SWAGGER_UI_SETTINGS': {'persistAuthorization': False, 'displayRequestDuration': True},
}


# Activar HTTPS/proxy solo cuando la infraestructura correspondiente este lista.
CSRF_TRUSTED_ORIGINS = [
    origen.strip()
    for origen in os.environ.get('DJANGO_CSRF_TRUSTED_ORIGINS', '').split(',')
    if origen.strip()
]
SECURE_SSL_REDIRECT = os.environ.get('DJANGO_SECURE_SSL_REDIRECT', 'False').lower() in ('true', '1', 'yes')
SESSION_COOKIE_SECURE = os.environ.get('DJANGO_SESSION_COOKIE_SECURE', str(not DEBUG)).lower() in ('true', '1', 'yes')
CSRF_COOKIE_SECURE = os.environ.get('DJANGO_CSRF_COOKIE_SECURE', str(not DEBUG)).lower() in ('true', '1', 'yes')
SECURE_HSTS_SECONDS = int(os.environ.get('DJANGO_SECURE_HSTS_SECONDS', '0'))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get('DJANGO_SECURE_HSTS_INCLUDE_SUBDOMAINS', 'False').lower() in ('true', '1', 'yes')
SECURE_HSTS_PRELOAD = os.environ.get('DJANGO_SECURE_HSTS_PRELOAD', 'False').lower() in ('true', '1', 'yes')
if os.environ.get('DJANGO_TRUST_PROXY', 'False').lower() in ('true', '1', 'yes'):
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

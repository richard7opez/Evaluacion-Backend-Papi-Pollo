"""
Django settings for config project.

Proyecto: Papi Pollo
"""

from pathlib import Path


# ==========================================================
# RUTA BASE DEL PROYECTO
# ==========================================================

BASE_DIR = Path(__file__).resolve().parent.parent


# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

SECRET_KEY = 'django-insecure-1*7#_zu01_(#ij^eb7$9yd$5p$*^#q@jenqui_31$nlqnv_0wf'

DEBUG = True

ALLOWED_HOSTS = []


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

    # Aplicaciones del proyecto Papi Pollo
    'menu',
    'sucursales',
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

        # Carpeta global de templates
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

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


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


# ==========================================================
# ARCHIVOS MULTIMEDIA
# IMÁGENES SUBIDAS DESDE DJANGO ADMIN
# ==========================================================

MEDIA_URL = '/media/'

MEDIA_ROOT = BASE_DIR / 'media'


# ==========================================================
# EMAIL
# ==========================================================

MAILERS = {
    'default': {
        'BACKEND': 'django.core.mail.backends.console.EmailBackend',
    },
}
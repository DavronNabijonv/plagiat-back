from pathlib import Path
from config.env import env

from config.conf.cors_headers import *
from config.conf.drf_yasg import *
from config.conf.jazzmin import *
from config.conf.logs import *
from config.conf.modern_drf_swagger import *
from config.conf.rest_framework import *
from config.conf.simplejwt import *
from config.conf.payme import *


BASE_DIR = Path(__file__).resolve().parent.parent
env.read_env(BASE_DIR / ".env")

SECRET_KEY = env.str("SECRET_KEY")
DEBUG = env.str("DEBUG")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS")


INSTALLED_APPS = [
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'rest_framework_simplejwt',
    'modern_drf_swagger',
    'drf_yasg',
    'corsheaders',
    'payme',
    # local apps
    'core.apps.users',
    'core.apps.shared',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / 'templates' ],
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


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
    }
}


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


LANGUAGE_CODE = 'uz'

TIME_ZONE = 'Asia/Tashkent'

USE_I18N = True

USE_TZ = True


STATIC_URL = 'resources/static/'
STATIC_ROOT = BASE_DIR / 'resources/static'


MEDIA_URL = 'resources/media/'
MEDIA_ROOT = BASE_DIR / 'resources/media'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'users.User'

PAYTECH_LICENSE_API_KEY='e472d69e-27b5-4d64-be96-e63a192e0f03'

LOGO_PATH = BASE_DIR / 'resources' / 'logo.png'

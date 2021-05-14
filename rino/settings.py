"""
Django settings for rino project.

Generated by 'django-admin startproject' using Django 3.0.3.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import environ

from django.contrib.messages import constants as messages

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'templates')
MEDIA_DIR = os.path.join(BASE_DIR, 'media')

env = environ.Env()
environ.Env.read_env()  # reading .env file

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

SECRET_KEY = env.str('RINO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['192.168.1.103', 'localhost', '192.168.1.108', 'djrino.azurewebsites.net', 'rino.skillnet.com.co', 'rino.skillnet.co']

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'crispy_forms',
    'core',
    'correspondence',
    'pqrs',
    'rest_framework',
    'django_filters',
    'django.contrib.postgres',
    'pinax.eventlog',
    'captcha',
    'storages',
    'corsheaders'
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'crum.CurrentRequestUserMiddleware',
]

ROOT_URLCONF = 'rino.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [TEMPLATE_DIR, ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'django.template.context_processors.media'
            ],
        },
    },
]

WSGI_APPLICATION = 'rino.wsgi.application'

DATABASES = env.json('RINO_DATABASES')

PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
    'django.contrib.auth.hashers.BCryptSHA256PasswordHasher',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 9}
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'es-co'

TIME_ZONE = 'America/Bogota'

USE_I18N = True

USE_L10N = True

USE_TZ = False

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, "assets")

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static")
]

MEDIA_ROOT = MEDIA_DIR
MEDIA_URL = '/media/'

LOGIN_URL = 'login'
LOGOUT_URL = 'logout'
LOGIN_REDIRECT_URL = '/correspondence/charts'

# X_FRAME_OPTIONS = 'SAMEORIGIN'
XS_SHARING_ALLOWED_METHODS = ['POST', 'GET', 'OPTIONS', 'PUT', 'DELETE']

# Config constants
ECM_USER = env.str('RINO_ECM_USER')
ECM_PASSWORD = env.str('RINO_ECM_PASSWORD')
ECM_SEARCH_URL = env.str('RINO_ECM_SEARCH_URL')
ECM_UPLOAD_URL = env.str('RINO_ECM_UPLOAD_URL')
ECM_RECORD_URL = env.str('RINO_ECM_RECORD_URL')
ECM_RECORD_ASSIGN_URL = env.str('RINO_ECM_RECORD_ASSIGN_URL')
ECM_RECORD_UPDATE_URL = env.str('RINO_ECM_RECORD_UPDATE_URL')
ECM_REQUEST_RENDITIONS = env.str('RINO_ECM_REQUEST_RENDITIONS')
ECM_PREVIEW_URL = env.str('RINO_ECM_PREVIEW_URL')

CONVERT_URL = 'http://localhost:3000/convert/office'

MESSAGE_TAGS = {
    messages.DEBUG: 'alert-info',
    messages.INFO: 'alert-info',
    messages.SUCCESS: 'alert-success',
    messages.WARNING: 'alert-warning',
    messages.ERROR: 'alert-danger',
}

# EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_USE_TLS = env.bool('RINO_EMAIL_USE_TLS')
EMAIL_HOST = env.str('RINO_EMAIL_HOST')
EMAIL_HOST_USER = env.str('RINO_EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env.str('RINO_EMAIL_HOST_PASSWORD')
EMAIL_PORT = env.int('RINO_EMAIL_PORT')
DEBUG = env.bool('RINO_DEBUG')

AUTH_USER_MODEL = 'auth.User'

DEFAULT_AUTO_FIELD = 'django.db.models.AutoField'


AZURE_STORAGE_KEY = env.bool('AZURE_STORAGE_KEY')


#DEFAULT_FILE_STORAGE = 'rino.custom_azure.AzureMediaStorage'
#STATICFILES_STORAGE = 'rino.custom_azure.AzureStaticStorage'

STATIC_LOCATION = "static"
MEDIA_LOCATION = "media"

AZURE_ACCOUNT_NAME = "storagerino"


#AZURE_CUSTOM_DOMAIN = f'{AZURE_ACCOUNT_NAME}.blob.core.windows.net'

#STATIC_URL = f'http://rino.skillnet.com.co/{STATIC_LOCATION}/'
#MEDIA_URL = f'http://rino.skillnet.com.co/{MEDIA_LOCATION}/'

CORS_ORIGIN_ALLOW_ALL = True

CORS_ORIGIN_WHITELIST = (
  'http://localhost:8000',
  'https://storagerino.blob.core.windows.net'
)

"""
Django settings for SS2DTournamentRunner project.

Generated by 'django-admin startproject' using Django 4.0.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

from pathlib import Path
import os
from dotenv import load_dotenv


# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
os.environ['DJ_BASE_DIR'] = str(BASE_DIR)

# add DOTENV_PATH to the user environ : DOTENV_PATH.
DOTENV_PATH = os.path.join(os.path.dirname(__file__), '.env')
if os.path.isfile(DOTENV_PATH):
    load_dotenv(DOTENV_PATH)
os.environ['DJ_DOTENV_PATH'] = DOTENV_PATH

EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_TLS = True
EMAIL_PORT = 587
DEFAULT_FROM_EMAIL = os.getenv('from_email')
EMAIL_HOST_USER = os.getenv('email_user')
EMAIL_HOST_PASSWORD = os.getenv('email_password')


# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = os.environ['SECRET_KEY'] # production
SECRET_KEY = 'django-insecure-jmjmb0b%mb+l9)jvm6y4rh+^02i6)wal5vf(^cs=d+m38j(bs4' # development

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# SECURITY WARNING: This is a security measure to prevent HTTP Host header attacks.
# A list of strings representing the host/domain names that this Django site can serve.
ALLOWED_HOSTS = ['127.0.0.1']
# A list of trusted origins for unsafe requests.
# CSRF_TRUSTED_ORIGINS = ['https://rcss.io']

# SECURITY WARNING: you may want to either set this setting True or configure a load balancer
# or reverse-proxy server to redirect all connections to HTTPS.
# SECURE_SSL_REDIRECT = True # production with SSL only

# SECURITY WARNING: Using a secure-only session cookie makes it more difficult for
# network traffic sniffers to hijack user sessions.
# SESSION_COOKIE_SECURE = True # production with SSL only

# SECURITY WARNING: Using a secure-only CSRF cookie makes it more difficult for network
# traffic sniffers to steal the CSRF token.
# CSRF_COOKIE_SECURE = True # production with SSL only

## HTTP Strict Transport Security
# SECURITY WARNING: If your entire site is served only over SSL,
# you may want to consider setting a value and enabling HTTP Strict Transport Security.
# SECURE_HSTS_SECONDS = 31536000 # production with SSL and HSTS

# SECURITY WARNING: Only set this to True if you are certain that all subdomains of your domain should be served exclusively via SSL.
# SECURE_HSTS_INCLUDE_SUBDOMAINS = True # production with SSL and HSTS

#  SECURITY WARNING: Without this, your site cannot be submitted to the browser preload list.
# SECURE_HSTS_PRELOAD = True # production with SSL and HSTS


# Application definition

INSTALLED_APPS = [
    'main.apps.MainConfig',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django_rq',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'SS2DTournamentRunner.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'SS2DTournamentRunner.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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


# Internationalization
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'assets/')

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, STATIC_URL),
]

# Media files (Client Uploads)
MEDIA_URL = '/upload/'
MEDIA_ROOT = os.path.join(BASE_DIR,'upload/')

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"


RQ_QUEUES = {
    'default': {
        'HOST': 'localhost',
        'PORT': 6379,
        'DB': 0,
        # 'PASSWORD': '',
        'DEFAULT_TIMEOUT': 600,
    },
}
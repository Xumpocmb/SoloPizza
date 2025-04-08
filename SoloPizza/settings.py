import os
from pathlib import Path
from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, '.env'))
SECRET_KEY = os.getenv('SECRET_KEY')
DEBUG = os.getenv('DEBUG') == 'True'

ALLOWED_HOSTS = ['*']
DOMAIN = 'solo-pizza.by'
SITE_NAME = 'Solo Pizza'
if DEBUG:
    DOMAIN_NAME = 'http://localhost:8000'
else:
    DOMAIN_NAME = os.getenv('DOMAIN_NAME')
SITEMAP_URLS = [
    'SoloPizza.sitemap.xml',
]

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'app_home.apps.AppHomeConfig',
    'app_catalog.apps.AppCatalogConfig',
    'app_user.apps.AppUserConfig',
    'app_cart.apps.AppCartConfig',
    'app_order.apps.AppOrderConfig'
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

ROOT_URLCONF = 'SoloPizza.urls'

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "app_home.context_processors.site_context_processor",
                "app_home.context_processors.carts_total",
            ],
        },
    },
]

WSGI_APPLICATION = 'SoloPizza.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
]

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 4,
        }
    },
]

LANGUAGE_CODE = 'ru-RU'
TIME_ZONE = 'Europe/Moscow'

USE_I18N = True
USE_TZ = False


STATIC_URL = 'static/'
if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / 'static',
    ]
else:
    STATIC_ROOT = BASE_DIR / 'static'

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


AUTH_USER_MODEL = 'app_user.CustomUser'

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGIN_URL = '/user/login/'

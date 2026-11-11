import os
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(os.path.join(BASE_DIR, ".env"))
SECRET_KEY = os.getenv("SECRET_KEY")
DEBUG = os.getenv("DEBUG") == "True"

ALLOWED_HOSTS = ["*"]
SITE_NAME = "Solo Pizza"
if DEBUG:
    DOMAIN_NAME = "http://localhost:8000"
else:
    DOMAIN_NAME = os.getenv("DOMAIN_NAME")
SITEMAP_URLS = [
    "SoloPizza.sitemap.xml",
]

SITE_ID = 1
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHAT_ID = os.getenv("CHAT_ID")
INSTAGRAM_URL = os.getenv("INSTAGRAM_URL", "https://www.instagram.com/solo_pizza_bar/")


INTERNAL_IPS = [
    "127.0.0.1",
]


INSTALLED_APPS = [
    "django.contrib.sites",
    "django.contrib.sitemaps",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "modeltranslation",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django_celery_results",
    "django_celery_beat",
    "debug_toolbar",
    "rest_framework",
    "rest_framework_simplejwt.token_blacklist",
    "drf_spectacular",
    "app_home.apps.AppHomeConfig",
    "app_catalog.apps.AppCatalogConfig",
    "app_user.apps.AppUserConfig",
    "app_cart.apps.AppCartConfig",
    "app_order.apps.AppOrderConfig",
    "app_reviews.apps.AppReviewsConfig",
    "app_api.apps.AppApiConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "SoloPizza.urls"

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
                "app_home.context_processors.site_settings_context_processor",
                "app_home.context_processors.canonical_context",
                "app_home.context_processors.cart_context",
                "app_home.context_processors.company_context",
                "app_home.context_processors.cookie_consent_context",
            ],
        },
    },
]

WSGI_APPLICATION = "SoloPizza.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": os.getenv("POSTGRES_DB", "solopizza"),
#         "USER": os.getenv("POSTGRES_USER", "soloadmin"),
#         "PASSWORD": os.getenv("POSTGRES_PASSWORD", "1234"),
#         "HOST": os.getenv("DB_HOST", "db"),
#         "PORT": os.getenv("DB_PORT", "5432"),
#     }
# }

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
        "OPTIONS": {
            "min_length": 4,
        },
    },
]

LANGUAGE_CODE = "ru-RU"
TIME_ZONE = "Europe/Minsk"

LANGUAGES = [
    ("ru", "Russian"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
if DEBUG:
    STATICFILES_DIRS = [
        BASE_DIR / "static",
    ]
else:
    STATIC_ROOT = BASE_DIR / "static"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# constants for the mobile app API
CURRENCY = "BYN"

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    # Публичные POST-эндпоинты ограничиваются по IP: read-only каталог не троттлится.
    # cart: корзину приложения меняют часто (каждое «добавить»/«+»), поэтому свой лимит по IP
    "DEFAULT_THROTTLE_RATES": {"anon": "10/min", "cart": "120/min", "auth": "20/min"},
}

# Вход в мобильном приложении: JWT (access короткий, refresh с ротацией и чёрным списком)
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=30),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
}
# Client ID из Google Cloud, которыми приложение получает id_token (через запятую: web, android, ios)
GOOGLE_OAUTH_CLIENT_IDS = [cid.strip() for cid in os.getenv("GOOGLE_OAUTH_CLIENT_IDS", "").split(",") if cid.strip()]
# aud в identity_token от Sign in with Apple = bundle id приложения
APPLE_BUNDLE_ID = os.getenv("APPLE_BUNDLE_ID", "by.solopizza.app")

SPECTACULAR_SETTINGS = {
    "TITLE": "SoloPizza mobile API",
    "DESCRIPTION": "API мобильного приложения: каталог, корзина, вход, вакансии, объявления и контакты",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LOGIN_URL = "/user/login/"


# Настройки allauth
ACCOUNT_LOGIN_METHODS = ["email"]
ACCOUNT_SIGNUP_FIELDS = ["email*", "username", "password1*", "password2*"]
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
LOGIN_REDIRECT_URL = "/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_SESSION_REMEMBER = None
ACCOUNT_DEFAULT_HTTP_PROTOCOL = "https"
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# HTTPS и защищённые cookie: в продакшене (за TLS терминалом / reverse proxy) включаем
# редирект http -> https и Secure-флаги для cookie сессии/CSRF. В локальной разработке
# (DEBUG=True) и тестах выключаем, чтобы работа по http://localhost:8000 и тестовый
# раннер не ломались.
SECURE_SSL_REDIRECT = os.getenv("SECURE_SSL_REDIRECT", "False") == "True"
SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "False") == "True"
CSRF_COOKIE_SECURE = os.getenv("CSRF_COOKIE_SECURE", "False") == "True"

SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": ["profile", "email"],
        "AUTH_PARAMS": {"access_type": "offline"},
    }
}

# Redis settings
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = os.getenv("REDIS_PORT", "6379")
REDIS_DB = os.getenv("REDIS_DB", "0")

# Cache settings
CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": "redis://127.0.0.1:6379/1",  # Use 127.0.0.1 instead of 'redis'
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# Настройки для кеширования страниц
CACHE_MIDDLEWARE_ALIAS = "default"
CACHE_MIDDLEWARE_SECONDS = 60 * 60 * 6  # 6 часов
CACHE_MIDDLEWARE_KEY_PREFIX = "solopizza"

# Celery settings
CELERY_BROKER_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}"
CELERY_RESULT_BACKEND = "django-db"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = TIME_ZONE

EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = os.getenv("EMAIL_PORT")
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
EMAIL_USE_SSL = os.getenv("EMAIL_USE_SSL")
EMAIL_RECIPIENTS_LIST = os.getenv("EMAIL_RECIPIENT", "").split(",")

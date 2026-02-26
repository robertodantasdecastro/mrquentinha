from pathlib import Path

import environ

ROOT_DIR = Path(__file__).resolve().parents[3]

env = environ.Env(
    DEBUG=(bool, False),
)
environ.Env.read_env(ROOT_DIR / ".env")

SECRET_KEY = env("SECRET_KEY", default="django-insecure-dev-only-change-me")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["localhost", "127.0.0.1"])
CSRF_TRUSTED_ORIGINS = env.list("CSRF_TRUSTED_ORIGINS", default=[])

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "apps.accounts.apps.AccountsConfig",
    "apps.catalog.apps.CatalogConfig",
    "apps.inventory.apps.InventoryConfig",
    "apps.procurement.apps.ProcurementConfig",
    "apps.orders.apps.OrdersConfig",
    "apps.production.apps.ProductionConfig",
    "apps.finance.apps.FinanceConfig",
    "apps.ocr_ai.apps.OcrAiConfig",
    "apps.portal.apps.PortalConfig",
    "apps.personal_finance.apps.PersonalFinanceConfig",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
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
        "DIRS": [ROOT_DIR / "templates"],
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

DATABASES = {"default": env.db("DATABASE_URL")}

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        )
    },
    {"NAME": ("django.contrib.auth.password_validation." "MinimumLengthValidator")},
    {"NAME": ("django.contrib.auth.password_validation." "CommonPasswordValidator")},
    {"NAME": ("django.contrib.auth.password_validation." "NumericPasswordValidator")},
]

LANGUAGE_CODE = "pt-br"
TIME_ZONE = "America/Sao_Paulo"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = ROOT_DIR / "staticfiles"

MEDIA_URL = "/media/"
MEDIA_ROOT = ROOT_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

PAYMENTS_PROVIDER_DEFAULT = env(
    "PAYMENTS_PROVIDER_DEFAULT",
    default="mock",
)
PAYMENTS_INTENT_TTL_MINUTES = env.int(
    "PAYMENTS_INTENT_TTL_MINUTES",
    default=15,
)
PAYMENTS_WEBHOOK_TOKEN = env(
    "PAYMENTS_WEBHOOK_TOKEN",
    default="dev-mrquentinha-webhook-token",
)

EMAIL_BACKEND = env(
    "EMAIL_BACKEND",
    default="django.core.mail.backends.console.EmailBackend",
)
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@mrquentinha.local")
PROCUREMENT_ALERT_FROM_EMAIL = env(
    "PROCUREMENT_ALERT_FROM_EMAIL",
    default=DEFAULT_FROM_EMAIL,
)
PROCUREMENT_WHATSAPP_WEBHOOK_URL = env(
    "PROCUREMENT_WHATSAPP_WEBHOOK_URL",
    default="",
)
PROCUREMENT_WHATSAPP_WEBHOOK_TOKEN = env(
    "PROCUREMENT_WHATSAPP_WEBHOOK_TOKEN",
    default="",
)

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
}

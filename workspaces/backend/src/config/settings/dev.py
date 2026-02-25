from .base import *  # noqa: F403
from .base import env

DEBUG = env.bool("DEBUG", default=True)

INSTALLED_APPS = [*INSTALLED_APPS, "corsheaders"]  # noqa: F405

CORS_MIDDLEWARE = "corsheaders.middleware.CorsMiddleware"
if CORS_MIDDLEWARE not in MIDDLEWARE:  # noqa: F405
    common_middleware = "django.middleware.common.CommonMiddleware"
    if common_middleware in MIDDLEWARE:  # noqa: F405
        common_index = MIDDLEWARE.index(common_middleware)  # noqa: F405
        MIDDLEWARE.insert(common_index, CORS_MIDDLEWARE)  # noqa: F405
    else:
        MIDDLEWARE.insert(0, CORS_MIDDLEWARE)  # noqa: F405

CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[
        "http://10.211.55.21:3000",
        "http://10.211.55.21:3001",
        "http://10.211.55.21:3002",
        "http://localhost:3000",
        "http://localhost:3001",
        "http://localhost:3002",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:3001",
        "http://127.0.0.1:3002",
    ],
)
CORS_ALLOW_CREDENTIALS = True

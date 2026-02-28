from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response


@api_view(["GET"])
@permission_classes([AllowAny])
def api_index_view(_request):
    return Response(
        {
            "app": "mrquentinha",
            "version": "v1",
            "endpoints": {
                "health": "/api/v1/health",
                "accounts": "/api/v1/accounts",
                "catalog": "/api/v1/catalog",
                "orders": "/api/v1/orders",
                "orders_ops_dashboard": "/api/v1/orders/ops/dashboard/",
                "orders_ops_realtime": "/api/v1/orders/ops/realtime/",
                "finance": "/api/v1/finance",
                "production": "/api/v1/production",
                "ocr": "/api/v1/ocr",
                "portal": "/api/v1/portal",
                "mobile_release_latest": "/api/v1/portal/mobile/releases/latest/",
                "personal_finance": "/api/v1/personal-finance",
                "admin_audit": "/api/v1/admin-audit/admin-activity/",
            },
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny])
def health_view(_request):
    return Response({"status": "ok", "app": "mrquentinha", "version": "v1"})


urlpatterns = [
    path("", api_index_view, name="api-index"),
    path(
        "favicon.ico",
        RedirectView.as_view(url="/static/brand/icon_symbol.svg", permanent=False),
        name="favicon",
    ),
    path("admin/", admin.site.urls),
    path("api/v1/health", health_view, name="health-check"),
    path("api/v1/accounts/", include("apps.accounts.urls")),
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/procurement/", include("apps.procurement.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/production/", include("apps.production.urls")),
    path("api/v1/finance/", include("apps.finance.urls")),
    path("api/v1/ocr/", include("apps.ocr_ai.urls")),
    path("api/v1/portal/", include("apps.portal.urls")),
    path("api/v1/personal-finance/", include("apps.personal_finance.urls")),
    path("api/v1/admin-audit/", include("apps.admin_audit.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

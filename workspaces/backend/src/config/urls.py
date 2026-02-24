from django.contrib import admin
from django.urls import include, path
from django.views.generic import RedirectView
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def api_index_view(_request):
    return Response(
        {
            "app": "mrquentinha",
            "version": "v1",
            "endpoints": {
                "health": "/api/v1/health",
                "catalog": "/api/v1/catalog",
                "orders": "/api/v1/orders",
                "finance": "/api/v1/finance",
                "production": "/api/v1/production",
            },
        }
    )


@api_view(["GET"])
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
    path("api/v1/catalog/", include("apps.catalog.urls")),
    path("api/v1/inventory/", include("apps.inventory.urls")),
    path("api/v1/procurement/", include("apps.procurement.urls")),
    path("api/v1/orders/", include("apps.orders.urls")),
    path("api/v1/production/", include("apps.production.urls")),
    path("api/v1/finance/", include("apps.finance.urls")),
]

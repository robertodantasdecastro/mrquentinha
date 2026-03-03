from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PurchaseRequestViewSet,
    PurchasesExportAPIView,
    PurchaseViewSet,
    SeedParaibaCaseiraWeekAPIView,
)

router = DefaultRouter()
router.register(r"requests", PurchaseRequestViewSet, basename="procurement-requests")
router.register(r"purchases", PurchaseViewSet, basename="procurement-purchases")

urlpatterns = [
    path(
        "ops/seed-paraiba-week/",
        SeedParaibaCaseiraWeekAPIView.as_view(),
        name="procurement-seed-paraiba-week",
    ),
    path(
        "reports/purchases/",
        PurchasesExportAPIView.as_view(),
        name="procurement-purchases-export",
    ),
    path("", include(router.urls)),
]

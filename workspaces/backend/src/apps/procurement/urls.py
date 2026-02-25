from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PurchaseRequestViewSet, PurchasesExportAPIView, PurchaseViewSet

router = DefaultRouter()
router.register(r"requests", PurchaseRequestViewSet, basename="procurement-requests")
router.register(r"purchases", PurchaseViewSet, basename="procurement-purchases")

urlpatterns = [
    path(
        "reports/purchases/",
        PurchasesExportAPIView.as_view(),
        name="procurement-purchases-export",
    ),
    path("", include(router.urls)),
]

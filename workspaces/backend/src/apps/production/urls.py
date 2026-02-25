from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductionBatchViewSet, ProductionExportAPIView

router = DefaultRouter()
router.register(r"batches", ProductionBatchViewSet, basename="production-batches")

urlpatterns = [
    path(
        "reports/production/",
        ProductionExportAPIView.as_view(),
        name="production-export",
    ),
    path("", include(router.urls)),
]

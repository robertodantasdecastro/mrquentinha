from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import StockItemViewSet, StockMovementViewSet

router = DefaultRouter()
router.register(r"stock-items", StockItemViewSet, basename="inventory-stock-items")
router.register(r"movements", StockMovementViewSet, basename="inventory-movements")

urlpatterns = [
    path("", include(router.urls)),
]

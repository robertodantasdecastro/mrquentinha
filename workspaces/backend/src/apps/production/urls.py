from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import ProductionBatchViewSet

router = DefaultRouter()
router.register(r"batches", ProductionBatchViewSet, basename="production-batches")

urlpatterns = [
    path("", include(router.urls)),
]

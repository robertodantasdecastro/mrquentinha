from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import PurchaseRequestViewSet, PurchaseViewSet

router = DefaultRouter()
router.register(r"requests", PurchaseRequestViewSet, basename="procurement-requests")
router.register(r"purchases", PurchaseViewSet, basename="procurement-purchases")

urlpatterns = [
    path("", include(router.urls)),
]

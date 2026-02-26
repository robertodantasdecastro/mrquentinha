from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    OrdersExportAPIView,
    OrdersOpsDashboardAPIView,
    OrderViewSet,
    PaymentViewSet,
    PaymentWebhookAPIView,
)

router = DefaultRouter()
router.register(r"orders", OrderViewSet, basename="orders-orders")
router.register(r"payments", PaymentViewSet, basename="orders-payments")

urlpatterns = [
    path(
        "payments/webhook/",
        PaymentWebhookAPIView.as_view(),
        name="orders-payments-webhook",
    ),
    path(
        "reports/orders/",
        OrdersExportAPIView.as_view(),
        name="orders-export",
    ),
    path(
        "ops/dashboard/",
        OrdersOpsDashboardAPIView.as_view(),
        name="orders-ops-dashboard",
    ),
    path("", include(router.urls)),
]

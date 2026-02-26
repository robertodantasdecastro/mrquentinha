from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AsaasWebhookAPIView,
    EcosystemOpsRealtimeAPIView,
    EfiWebhookAPIView,
    MercadoPagoWebhookAPIView,
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
        "payments/webhook/mercadopago/",
        MercadoPagoWebhookAPIView.as_view(),
        name="orders-payments-webhook-mercadopago",
    ),
    path(
        "payments/webhook/asaas/",
        AsaasWebhookAPIView.as_view(),
        name="orders-payments-webhook-asaas",
    ),
    path(
        "payments/webhook/efi/",
        EfiWebhookAPIView.as_view(),
        name="orders-payments-webhook-efi",
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
    path(
        "ops/realtime/",
        EcosystemOpsRealtimeAPIView.as_view(),
        name="orders-ops-realtime",
    ),
    path("", include(router.urls)),
]

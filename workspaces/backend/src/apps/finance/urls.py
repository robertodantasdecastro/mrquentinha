from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    APBillViewSet,
    ARReceivableViewSet,
    CashMovementViewSet,
)

router = DefaultRouter()
router.register(r"accounts", AccountViewSet, basename="finance-accounts")
router.register(r"ap-bills", APBillViewSet, basename="finance-ap-bills")
router.register(
    r"ar-receivables",
    ARReceivableViewSet,
    basename="finance-ar-receivables",
)
router.register(
    r"cash-movements",
    CashMovementViewSet,
    basename="finance-cash-movements",
)

urlpatterns = [
    path("", include(router.urls)),
]

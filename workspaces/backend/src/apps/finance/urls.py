from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    APBillViewSet,
    ARReceivableViewSet,
    BankStatementViewSet,
    CashflowReportAPIView,
    CashMovementViewSet,
    DreReportAPIView,
    KpisReportAPIView,
    LedgerEntryViewSet,
    StatementLineViewSet,
    UnreconciledReportAPIView,
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
    r"bank-statements",
    BankStatementViewSet,
    basename="finance-bank-statements",
)
router.register(
    r"statement-lines",
    StatementLineViewSet,
    basename="finance-statement-lines",
)
router.register(
    r"cash-movements",
    CashMovementViewSet,
    basename="finance-cash-movements",
)
router.register(r"ledger", LedgerEntryViewSet, basename="finance-ledger")

urlpatterns = [
    path("reports/cashflow/", CashflowReportAPIView.as_view(), name="finance-cashflow"),
    path(
        "reports/unreconciled/",
        UnreconciledReportAPIView.as_view(),
        name="finance-unreconciled",
    ),
    path("reports/dre/", DreReportAPIView.as_view(), name="finance-dre"),
    path("reports/kpis/", KpisReportAPIView.as_view(), name="finance-kpis"),
    path("", include(router.urls)),
]

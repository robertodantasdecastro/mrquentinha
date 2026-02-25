from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    AccountViewSet,
    APBillViewSet,
    ARReceivableViewSet,
    BankStatementViewSet,
    CashflowExportAPIView,
    CashflowReportAPIView,
    CashMovementViewSet,
    DreExportAPIView,
    DreReportAPIView,
    FinancialCloseViewSet,
    IsClosedAPIView,
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
router.register(r"closes", FinancialCloseViewSet, basename="finance-closes")

urlpatterns = [
    path("reports/cashflow/", CashflowReportAPIView.as_view(), name="finance-cashflow"),
    path(
        "reports/cashflow/export/",
        CashflowExportAPIView.as_view(),
        name="finance-cashflow-export",
    ),
    path(
        "reports/unreconciled/",
        UnreconciledReportAPIView.as_view(),
        name="finance-unreconciled",
    ),
    path("reports/dre/", DreReportAPIView.as_view(), name="finance-dre"),
    path(
        "reports/dre/export/",
        DreExportAPIView.as_view(),
        name="finance-dre-export",
    ),
    path("reports/kpis/", KpisReportAPIView.as_view(), name="finance-kpis"),
    path("closes/is-closed/", IsClosedAPIView.as_view(), name="finance-is-closed"),
    path("", include(router.urls)),
]

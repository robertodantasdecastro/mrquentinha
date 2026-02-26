from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    PersonalAccountViewSet,
    PersonalAuditLogViewSet,
    PersonalBudgetViewSet,
    PersonalCategoryViewSet,
    PersonalDataExportAPIView,
    PersonalEntryViewSet,
    PersonalImportConfirmAPIView,
    PersonalImportJobViewSet,
    PersonalImportPreviewAPIView,
    PersonalMonthlySummaryAPIView,
    PersonalRecurringRuleViewSet,
)

router = DefaultRouter()
router.register(
    r"accounts", PersonalAccountViewSet, basename="personal-finance-accounts"
)
router.register(
    r"categories",
    PersonalCategoryViewSet,
    basename="personal-finance-categories",
)
router.register(r"entries", PersonalEntryViewSet, basename="personal-finance-entries")
router.register(
    r"recurring-rules",
    PersonalRecurringRuleViewSet,
    basename="personal-finance-recurring-rules",
)
router.register(r"budgets", PersonalBudgetViewSet, basename="personal-finance-budgets")
router.register(
    r"audit-logs",
    PersonalAuditLogViewSet,
    basename="personal-finance-audit-logs",
)
router.register(
    r"imports",
    PersonalImportJobViewSet,
    basename="personal-finance-import-jobs",
)

urlpatterns = [
    path(
        "export/", PersonalDataExportAPIView.as_view(), name="personal-finance-export"
    ),
    path(
        "summary/monthly/",
        PersonalMonthlySummaryAPIView.as_view(),
        name="personal-finance-summary-monthly",
    ),
    path(
        "imports/preview/",
        PersonalImportPreviewAPIView.as_view(),
        name="personal-finance-import-preview",
    ),
    path(
        "imports/<int:job_id>/confirm/",
        PersonalImportConfirmAPIView.as_view(),
        name="personal-finance-import-confirm",
    ),
    path("", include(router.urls)),
]

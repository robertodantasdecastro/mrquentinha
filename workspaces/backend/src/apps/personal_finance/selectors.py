from datetime import date, datetime

from django.db.models import QuerySet

from .models import (
    PersonalAccount,
    PersonalAuditLog,
    PersonalBudget,
    PersonalCategory,
    PersonalEntry,
    PersonalImportJob,
    PersonalRecurringRule,
)


def list_personal_accounts(*, owner) -> QuerySet[PersonalAccount]:
    return PersonalAccount.objects.filter(owner=owner).order_by("name", "id")


def list_personal_categories(*, owner) -> QuerySet[PersonalCategory]:
    return PersonalCategory.objects.filter(owner=owner).order_by("name", "id")


def list_personal_entries(
    *,
    owner,
    from_date: date | None = None,
    to_date: date | None = None,
    direction: str | None = None,
) -> QuerySet[PersonalEntry]:
    queryset = PersonalEntry.objects.select_related("account", "category").filter(
        owner=owner
    )

    if from_date is not None:
        queryset = queryset.filter(entry_date__gte=from_date)

    if to_date is not None:
        queryset = queryset.filter(entry_date__lte=to_date)

    if direction:
        queryset = queryset.filter(direction=direction)

    return queryset.order_by("-entry_date", "-id")


def list_personal_recurring_rules(*, owner) -> QuerySet[PersonalRecurringRule]:
    return (
        PersonalRecurringRule.objects.select_related("account", "category")
        .filter(owner=owner)
        .order_by("next_run_date", "id")
    )


def list_personal_import_jobs(*, owner) -> QuerySet[PersonalImportJob]:
    return PersonalImportJob.objects.filter(owner=owner).order_by("-created_at", "-id")


def list_personal_budgets(*, owner) -> QuerySet[PersonalBudget]:
    return (
        PersonalBudget.objects.select_related("category")
        .filter(owner=owner)
        .order_by("-month_ref", "-id")
    )


def list_personal_audit_logs(*, owner) -> QuerySet[PersonalAuditLog]:
    return PersonalAuditLog.objects.filter(owner=owner).order_by("-created_at", "-id")


def list_personal_audit_logs_older_than(
    *,
    cutoff: datetime,
) -> QuerySet[PersonalAuditLog]:
    return PersonalAuditLog.objects.filter(created_at__lt=cutoff)

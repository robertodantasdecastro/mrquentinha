from django.contrib import admin

from .models import (
    PersonalAccount,
    PersonalAuditLog,
    PersonalBudget,
    PersonalCategory,
    PersonalEntry,
    PersonalImportJob,
    PersonalRecurringRule,
)


@admin.register(PersonalAccount)
class PersonalAccountAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "name", "type", "is_active", "created_at")
    search_fields = ("name", "owner__username", "owner__email")
    list_filter = ("type", "is_active")


@admin.register(PersonalCategory)
class PersonalCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "owner", "name", "direction", "is_active", "created_at")
    search_fields = ("name", "owner__username", "owner__email")
    list_filter = ("direction", "is_active")


@admin.register(PersonalEntry)
class PersonalEntryAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "entry_date",
        "direction",
        "amount",
        "account",
        "category",
        "recurring_rule",
        "import_job",
        "created_at",
    )
    search_fields = ("description", "owner__username", "owner__email")
    list_filter = ("direction", "entry_date")


@admin.register(PersonalBudget)
class PersonalBudgetAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "category",
        "month_ref",
        "limit_amount",
        "created_at",
    )
    search_fields = ("owner__username", "owner__email", "category__name")
    list_filter = ("month_ref",)


@admin.register(PersonalAuditLog)
class PersonalAuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "event_type",
        "resource_type",
        "resource_id",
        "created_at",
    )
    search_fields = ("owner__username", "owner__email", "resource_type")
    list_filter = ("event_type", "resource_type")


@admin.register(PersonalRecurringRule)
class PersonalRecurringRuleAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "frequency",
        "interval",
        "next_run_date",
        "amount",
        "is_active",
        "created_at",
    )
    search_fields = ("owner__username", "owner__email", "description")
    list_filter = ("frequency", "is_active")


@admin.register(PersonalImportJob)
class PersonalImportJobAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "owner",
        "status",
        "source_filename",
        "rows_total",
        "rows_valid",
        "rows_invalid",
        "imported_count",
        "skipped_count",
        "created_at",
    )
    search_fields = ("owner__username", "owner__email", "source_filename")
    list_filter = ("status", "delimiter")

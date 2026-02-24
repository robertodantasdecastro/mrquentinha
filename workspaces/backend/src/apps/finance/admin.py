from django.contrib import admin

from .models import (
    Account,
    APBill,
    ARReceivable,
    BankStatement,
    CashMovement,
    LedgerEntry,
    StatementLine,
)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "type", "is_active", "created_at"]
    list_filter = ["type", "is_active"]
    search_fields = ["name"]


@admin.register(APBill)
class APBillAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "supplier_name",
        "account",
        "amount",
        "due_date",
        "status",
        "reference_type",
        "reference_id",
    ]
    list_filter = ["status", "due_date", "account"]
    search_fields = ["supplier_name", "reference_type", "reference_id"]


@admin.register(ARReceivable)
class ARReceivableAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "customer",
        "account",
        "amount",
        "due_date",
        "status",
        "reference_type",
        "reference_id",
    ]
    list_filter = ["status", "due_date", "account"]
    search_fields = ["customer__username", "customer__email", "reference_type"]


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "period_start",
        "period_end",
        "opening_balance",
        "closing_balance",
        "source",
        "created_at",
    ]
    list_filter = ["period_start", "period_end", "source"]
    search_fields = ["source"]


@admin.register(StatementLine)
class StatementLineAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "statement",
        "line_date",
        "description",
        "amount",
        "created_at",
    ]
    list_filter = ["line_date", "statement"]
    search_fields = ["description"]


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "movement_date",
        "direction",
        "amount",
        "account",
        "is_reconciled",
        "statement_line",
        "reference_type",
        "reference_id",
    ]
    list_filter = ["direction", "movement_date", "account", "is_reconciled"]
    search_fields = ["reference_type", "reference_id", "note"]


@admin.register(LedgerEntry)
class LedgerEntryAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "entry_date",
        "entry_type",
        "amount",
        "debit_account",
        "credit_account",
        "reference_type",
        "reference_id",
    ]
    list_filter = ["entry_type", "entry_date", "debit_account", "credit_account"]
    search_fields = ["reference_type", "reference_id", "note"]

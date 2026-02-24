from django.contrib import admin

from .models import Account, APBill, ARReceivable, CashMovement, LedgerEntry


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


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "movement_date",
        "direction",
        "amount",
        "account",
        "reference_type",
        "reference_id",
    ]
    list_filter = ["direction", "movement_date", "account"]
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

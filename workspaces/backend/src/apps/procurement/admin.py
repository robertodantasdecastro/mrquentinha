from django.contrib import admin

from .models import Purchase, PurchaseItem, PurchaseRequest, PurchaseRequestItem


class PurchaseRequestItemInline(admin.TabularInline):
    model = PurchaseRequestItem
    extra = 1


@admin.register(PurchaseRequest)
class PurchaseRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "requested_by", "requested_at")
    list_filter = ("status",)
    search_fields = ("id", "note")
    inlines = [PurchaseRequestItemInline]


class PurchaseItemInline(admin.TabularInline):
    model = PurchaseItem
    extra = 1


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "supplier_name",
        "invoice_number",
        "purchase_date",
        "total_amount",
    )
    search_fields = ("supplier_name", "invoice_number")
    inlines = [PurchaseItemInline]


@admin.register(PurchaseRequestItem)
class PurchaseRequestItemAdmin(admin.ModelAdmin):
    list_display = ("id", "purchase_request", "ingredient", "required_qty", "unit")
    search_fields = ("purchase_request__id", "ingredient__name")


@admin.register(PurchaseItem)
class PurchaseItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "purchase",
        "ingredient",
        "qty",
        "unit",
        "unit_price",
    )
    search_fields = ("purchase__id", "ingredient__name")

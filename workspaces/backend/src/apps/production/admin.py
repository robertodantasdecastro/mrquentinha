from django.contrib import admin

from .models import ProductionBatch, ProductionItem


class ProductionItemInline(admin.TabularInline):
    model = ProductionItem
    extra = 1


@admin.register(ProductionBatch)
class ProductionBatchAdmin(admin.ModelAdmin):
    list_display = ("id", "production_date", "status", "created_by", "created_at")
    list_filter = ("status", "production_date")
    search_fields = ("id", "note")
    inlines = [ProductionItemInline]


@admin.register(ProductionItem)
class ProductionItemAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "batch",
        "menu_item",
        "qty_planned",
        "qty_produced",
        "qty_waste",
    )
    search_fields = ("batch__id", "menu_item__dish__name")

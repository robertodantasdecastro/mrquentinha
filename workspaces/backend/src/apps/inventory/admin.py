from django.contrib import admin

from .models import StockItem, StockMovement


@admin.register(StockItem)
class StockItemAdmin(admin.ModelAdmin):
    list_display = ("id", "ingredient", "balance_qty", "unit", "min_qty", "updated_at")
    search_fields = ("ingredient__name",)
    list_filter = ("unit",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "ingredient",
        "movement_type",
        "qty",
        "unit",
        "reference_type",
        "reference_id",
        "created_at",
    )
    search_fields = ("ingredient__name", "reference_id")
    list_filter = ("movement_type", "reference_type", "unit")

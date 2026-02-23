from django.contrib import admin

from .models import Dish, DishIngredient, Ingredient, MenuDay, MenuItem


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "unit", "is_active", "updated_at")
    list_filter = ("unit", "is_active")
    search_fields = ("name",)


class DishIngredientInline(admin.TabularInline):
    model = DishIngredient
    extra = 1


@admin.register(Dish)
class DishAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "yield_portions", "updated_at")
    search_fields = ("name",)
    inlines = [DishIngredientInline]


class MenuItemInline(admin.TabularInline):
    model = MenuItem
    extra = 1


@admin.register(MenuDay)
class MenuDayAdmin(admin.ModelAdmin):
    list_display = ("id", "menu_date", "title", "created_by", "updated_at")
    search_fields = ("title",)
    inlines = [MenuItemInline]


@admin.register(DishIngredient)
class DishIngredientAdmin(admin.ModelAdmin):
    list_display = ("id", "dish", "ingredient", "quantity", "unit")
    search_fields = ("dish__name", "ingredient__name")


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    list_display = ("id", "menu_day", "dish", "sale_price", "is_active")
    list_filter = ("is_active",)
    search_fields = ("dish__name", "menu_day__title")

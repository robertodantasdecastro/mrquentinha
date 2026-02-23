from django.db.models import F, QuerySet

from apps.catalog.models import Ingredient

from .models import StockItem


def get_stock_by_ingredient(ingredient: Ingredient | int) -> StockItem | None:
    ingredient_id = ingredient.id if isinstance(ingredient, Ingredient) else ingredient
    return (
        StockItem.objects.filter(ingredient_id=ingredient_id)
        .select_related("ingredient")
        .first()
    )


def list_low_stock() -> QuerySet[StockItem]:
    return (
        StockItem.objects.filter(min_qty__isnull=False, balance_qty__lte=F("min_qty"))
        .select_related("ingredient")
        .order_by("ingredient__name")
    )

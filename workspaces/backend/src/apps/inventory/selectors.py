from collections.abc import Iterable

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


def get_stock_map_by_ingredient_ids(
    ingredient_ids: Iterable[int],
) -> dict[int, StockItem]:
    ingredient_id_set = {int(ingredient_id) for ingredient_id in ingredient_ids}
    if not ingredient_id_set:
        return {}

    stock_items = (
        StockItem.objects.filter(ingredient_id__in=ingredient_id_set)
        .select_related("ingredient")
        .order_by("ingredient_id")
    )
    return {stock_item.ingredient_id: stock_item for stock_item in stock_items}


def list_low_stock() -> QuerySet[StockItem]:
    return (
        StockItem.objects.filter(min_qty__isnull=False, balance_qty__lte=F("min_qty"))
        .select_related("ingredient")
        .order_by("ingredient__name")
    )

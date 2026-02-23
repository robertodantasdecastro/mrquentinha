from datetime import date

from django.db.models import Prefetch, QuerySet

from .models import Ingredient, MenuDay, MenuItem


def list_active_ingredients() -> QuerySet[Ingredient]:
    return Ingredient.objects.filter(is_active=True).order_by("name")


def get_menu_by_date(menu_date: date | str) -> MenuDay | None:
    parsed_date = (
        date.fromisoformat(menu_date) if isinstance(menu_date, str) else menu_date
    )
    active_items_qs = MenuItem.objects.filter(is_active=True).select_related("dish")
    return (
        MenuDay.objects.filter(menu_date=parsed_date)
        .select_related("created_by")
        .prefetch_related(Prefetch("items", queryset=active_items_qs))
        .first()
    )

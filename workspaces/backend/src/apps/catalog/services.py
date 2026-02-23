from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Dish, DishIngredient, MenuDay, MenuItem


def _assert_unique_ingredients_payload(ingredients_payload: list[dict]) -> None:
    ingredient_ids = [item["ingredient"].id for item in ingredients_payload]
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError("Ingrediente duplicado no payload do prato.")


def _assert_unique_menu_items_payload(items_payload: list[dict]) -> None:
    dish_ids = [item["dish"].id for item in items_payload]
    if len(dish_ids) != len(set(dish_ids)):
        raise ValidationError("Prato duplicado no payload do cardapio.")


@transaction.atomic
def _replace_dish_ingredients(dish: Dish, ingredients_payload: list[dict]) -> None:
    if not ingredients_payload:
        raise ValidationError("Prato deve possuir ao menos um ingrediente.")

    _assert_unique_ingredients_payload(ingredients_payload)
    DishIngredient.objects.filter(dish=dish).delete()
    DishIngredient.objects.bulk_create(
        [
            DishIngredient(
                dish=dish,
                ingredient=item["ingredient"],
                quantity=item["quantity"],
                unit=item.get("unit") or None,
            )
            for item in ingredients_payload
        ]
    )


@transaction.atomic
def create_dish_with_ingredients(
    dish_data: dict,
    ingredients_payload: list[dict],
) -> Dish:
    dish = Dish.objects.create(**dish_data)
    _replace_dish_ingredients(dish, ingredients_payload)
    return Dish.objects.prefetch_related("dish_ingredients__ingredient").get(pk=dish.pk)


@transaction.atomic
def update_dish_with_ingredients(
    dish: Dish,
    dish_data: dict,
    ingredients_payload: list[dict] | None,
) -> Dish:
    for field, value in dish_data.items():
        setattr(dish, field, value)
    dish.save()

    if ingredients_payload is not None:
        _replace_dish_ingredients(dish, ingredients_payload)

    return Dish.objects.prefetch_related("dish_ingredients__ingredient").get(pk=dish.pk)


@transaction.atomic
def _replace_menu_items(menu_day: MenuDay, items_payload: list[dict]) -> None:
    _assert_unique_menu_items_payload(items_payload)
    MenuItem.objects.filter(menu_day=menu_day).delete()
    MenuItem.objects.bulk_create(
        [
            MenuItem(
                menu_day=menu_day,
                dish=item["dish"],
                sale_price=item["sale_price"],
                available_qty=item.get("available_qty"),
                is_active=item.get("is_active", True),
            )
            for item in items_payload
        ]
    )


@transaction.atomic
def set_menu_for_day(
    menu_date: date,
    title: str,
    items_payload: list[dict] | None,
    *,
    created_by=None,
    menu_day: MenuDay | None = None,
) -> MenuDay:
    if menu_day is None:
        menu_day, _ = MenuDay.objects.get_or_create(
            menu_date=menu_date,
            defaults={"title": title, "created_by": created_by},
        )

    menu_day.menu_date = menu_date
    menu_day.title = title
    if created_by is not None:
        menu_day.created_by = created_by
    menu_day.save()

    if items_payload is not None:
        _replace_menu_items(menu_day, items_payload)
    return MenuDay.objects.prefetch_related("items__dish").get(pk=menu_day.pk)

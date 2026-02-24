from datetime import date
from decimal import Decimal

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


def _assert_recipe_unit_compatible(
    *, ingredient_unit: str, recipe_unit: str, ingredient_name: str
) -> None:
    if ingredient_unit != recipe_unit:
        raise ValidationError(
            f"Unidade incompativel para ingrediente '{ingredient_name}': "
            f"ingrediente em '{ingredient_unit}' e receita em '{recipe_unit}'. "
            "TODO: implementar conversao de unidades."
        )


def estimate_dish_nutrition_per_portion(*, dish: Dish) -> dict[str, Decimal]:
    dish = (
        Dish.objects.prefetch_related("dish_ingredients__ingredient__nutrition_fact")
        .filter(pk=dish.id)
        .first()
    )
    if dish is None:
        raise ValidationError("Prato nao encontrado para estimativa nutricional.")

    if dish.yield_portions <= 0:
        raise ValidationError("yield_portions deve ser maior que zero.")

    totals = {
        "energy_kcal": Decimal("0"),
        "carbs_g": Decimal("0"),
        "protein_g": Decimal("0"),
        "fat_g": Decimal("0"),
        "sat_fat_g": Decimal("0"),
        "fiber_g": Decimal("0"),
        "sodium_mg": Decimal("0"),
    }

    for dish_ingredient in dish.dish_ingredients.all():
        ingredient = dish_ingredient.ingredient
        nutrition_fact = getattr(ingredient, "nutrition_fact", None)
        if nutrition_fact is None:
            continue

        recipe_unit = dish_ingredient.unit or ingredient.unit
        _assert_recipe_unit_compatible(
            ingredient_unit=ingredient.unit,
            recipe_unit=recipe_unit,
            ingredient_name=ingredient.name,
        )

        if recipe_unit not in {"g", "ml"}:
            raise ValidationError(
                f"Ingrediente '{ingredient.name}' usa unidade '{recipe_unit}'. "
                "Sem conversao no MVP, use g/ml para estimativa nutricional."
            )

        qty_multiplier = Decimal(dish_ingredient.quantity) / Decimal("100")

        totals["energy_kcal"] += (
            nutrition_fact.energy_kcal_100g or Decimal("0")
        ) * qty_multiplier
        totals["carbs_g"] += (
            nutrition_fact.carbs_g_100g or Decimal("0")
        ) * qty_multiplier
        totals["protein_g"] += (
            nutrition_fact.protein_g_100g or Decimal("0")
        ) * qty_multiplier
        totals["fat_g"] += (nutrition_fact.fat_g_100g or Decimal("0")) * qty_multiplier
        totals["sat_fat_g"] += (
            nutrition_fact.sat_fat_g_100g or Decimal("0")
        ) * qty_multiplier
        totals["fiber_g"] += (
            nutrition_fact.fiber_g_100g or Decimal("0")
        ) * qty_multiplier
        totals["sodium_mg"] += (
            nutrition_fact.sodium_mg_100g or Decimal("0")
        ) * qty_multiplier

    return {
        key: (value / Decimal(dish.yield_portions)).quantize(Decimal("0.01"))
        for key, value in totals.items()
    }

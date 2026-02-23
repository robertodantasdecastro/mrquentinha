from datetime import date
from decimal import Decimal

import pytest

from apps.catalog.models import Ingredient, IngredientUnit
from apps.catalog.selectors import get_menu_by_date, list_active_ingredients
from apps.catalog.services import create_dish_with_ingredients, set_menu_for_day


@pytest.mark.django_db
def test_create_dish_with_ingredients_service_cria_relacionamentos():
    cenoura = Ingredient.objects.create(name="cenoura", unit=IngredientUnit.KILOGRAM)
    arroz = Ingredient.objects.create(name="arroz", unit=IngredientUnit.KILOGRAM)

    dish = create_dish_with_ingredients(
        dish_data={
            "name": "Arroz com Cenoura",
            "description": "Receita simples",
            "yield_portions": 8,
        },
        ingredients_payload=[
            {
                "ingredient": cenoura,
                "quantity": Decimal("1.250"),
                "unit": "kg",
            },
            {
                "ingredient": arroz,
                "quantity": Decimal("0.800"),
                "unit": "kg",
            },
        ],
    )

    assert dish.dish_ingredients.count() == 2
    assert dish.dish_ingredients.filter(ingredient=cenoura).exists()
    assert dish.dish_ingredients.filter(ingredient=arroz).exists()


@pytest.mark.django_db
def test_set_menu_for_day_e_selector_by_date_retorna_so_itens_ativos():
    abobora = Ingredient.objects.create(name="abobora", unit=IngredientUnit.KILOGRAM)
    carne = Ingredient.objects.create(name="carne", unit=IngredientUnit.KILOGRAM)

    prato_ativo = create_dish_with_ingredients(
        dish_data={
            "name": "Pure de Abobora",
            "description": "Acompanhamento",
            "yield_portions": 10,
        },
        ingredients_payload=[
            {
                "ingredient": abobora,
                "quantity": Decimal("1.000"),
                "unit": "kg",
            }
        ],
    )
    prato_inativo = create_dish_with_ingredients(
        dish_data={
            "name": "Carne Assada",
            "description": "Prato principal",
            "yield_portions": 10,
        },
        ingredients_payload=[
            {
                "ingredient": carne,
                "quantity": Decimal("1.000"),
                "unit": "kg",
            }
        ],
    )

    set_menu_for_day(
        menu_date=date(2026, 2, 23),
        title="Cardapio de Segunda",
        items_payload=[
            {
                "dish": prato_ativo,
                "sale_price": Decimal("22.90"),
                "available_qty": 25,
                "is_active": True,
            },
            {
                "dish": prato_inativo,
                "sale_price": Decimal("25.90"),
                "available_qty": 20,
                "is_active": False,
            },
        ],
    )

    menu = get_menu_by_date(date(2026, 2, 23))

    assert menu is not None
    assert menu.title == "Cardapio de Segunda"
    assert len(menu.items.all()) == 1
    assert menu.items.all()[0].dish.name == "Pure de Abobora"


@pytest.mark.django_db
def test_list_active_ingredients_selector_retorna_apenas_ativos_ordenados():
    Ingredient.objects.create(
        name="cebola", unit=IngredientUnit.KILOGRAM, is_active=True
    )
    Ingredient.objects.create(
        name="alho", unit=IngredientUnit.KILOGRAM, is_active=False
    )
    Ingredient.objects.create(
        name="batata", unit=IngredientUnit.KILOGRAM, is_active=True
    )

    ingredientes = list_active_ingredients()

    assert list(ingredientes.values_list("name", flat=True)) == ["batata", "cebola"]

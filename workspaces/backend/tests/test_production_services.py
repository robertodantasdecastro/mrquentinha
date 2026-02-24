from datetime import date
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.inventory.models import (
    StockItem,
    StockMovement,
    StockMovementType,
    StockReferenceType,
)
from apps.production.models import ProductionBatchStatus
from apps.production.services import complete_batch, create_batch_for_date


def _create_menu_item_for_production(
    *,
    menu_date: date,
    dish_name: str,
    ingredient_name: str,
    recipe_qty: Decimal,
) -> tuple[MenuItem, Ingredient]:
    ingredient = Ingredient.objects.create(
        name=ingredient_name,
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name=dish_name, yield_portions=10)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=recipe_qty,
        unit=IngredientUnit.KILOGRAM,
    )
    menu_day = MenuDay.objects.create(menu_date=menu_date, title="Cardapio Producao")
    menu_item = MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("22.00"),
        is_active=True,
    )
    return menu_item, ingredient


@pytest.mark.django_db
def test_create_batch_for_date_valida_menu_day_e_cria_itens():
    production_date = date(2026, 3, 15)
    menu_item, _ = _create_menu_item_for_production(
        menu_date=production_date,
        dish_name="Prato Producao 1",
        ingredient_name="Ingrediente Producao 1",
        recipe_qty=Decimal("1.000"),
    )

    batch = create_batch_for_date(
        production_date=production_date,
        note="Lote da cozinha",
        items_payload=[
            {
                "menu_item": menu_item,
                "qty_planned": 20,
                "qty_produced": 18,
                "qty_waste": 1,
            }
        ],
    )

    assert batch.production_date == production_date
    assert batch.status == ProductionBatchStatus.PLANNED
    assert batch.items.count() == 1
    item = batch.items.first()
    assert item.menu_item_id == menu_item.id
    assert item.qty_planned == 20
    assert item.qty_produced == 18
    assert item.qty_waste == 1


@pytest.mark.django_db
def test_complete_batch_gera_movimento_out_e_reduz_saldo():
    production_date = date(2026, 3, 16)
    menu_item, ingredient = _create_menu_item_for_production(
        menu_date=production_date,
        dish_name="Prato Producao 2",
        ingredient_name="Ingrediente Producao 2",
        recipe_qty=Decimal("1.500"),
    )
    StockItem.objects.create(
        ingredient=ingredient,
        balance_qty=Decimal("10.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    batch = create_batch_for_date(
        production_date=production_date,
        items_payload=[
            {
                "menu_item": menu_item,
                "qty_planned": 10,
                "qty_produced": 2,
            }
        ],
    )

    completed_batch = complete_batch(batch_id=batch.id)

    assert completed_batch.status == ProductionBatchStatus.DONE

    movement = StockMovement.objects.get(
        movement_type=StockMovementType.OUT,
        reference_type=StockReferenceType.PRODUCTION,
        reference_id=batch.id,
        ingredient=ingredient,
    )
    assert movement.qty == Decimal("3.000")

    stock_item = StockItem.objects.get(ingredient=ingredient)
    assert stock_item.balance_qty == Decimal("7.000")


@pytest.mark.django_db
def test_complete_batch_nao_permite_saldo_negativo():
    production_date = date(2026, 3, 17)
    menu_item, ingredient = _create_menu_item_for_production(
        menu_date=production_date,
        dish_name="Prato Producao 3",
        ingredient_name="Ingrediente Producao 3",
        recipe_qty=Decimal("2.000"),
    )
    StockItem.objects.create(
        ingredient=ingredient,
        balance_qty=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    batch = create_batch_for_date(
        production_date=production_date,
        items_payload=[
            {
                "menu_item": menu_item,
                "qty_planned": 5,
                "qty_produced": 1,
            }
        ],
    )

    with pytest.raises(ValidationError):
        complete_batch(batch_id=batch.id)

    batch.refresh_from_db()
    assert batch.status == ProductionBatchStatus.PLANNED
    assert (
        StockMovement.objects.filter(
            reference_type=StockReferenceType.PRODUCTION,
            reference_id=batch.id,
        ).count()
        == 0
    )


@pytest.mark.django_db
def test_complete_batch_duas_vezes_nao_duplica_movimentos():
    production_date = date(2026, 3, 18)
    menu_item, ingredient = _create_menu_item_for_production(
        menu_date=production_date,
        dish_name="Prato Producao 4",
        ingredient_name="Ingrediente Producao 4",
        recipe_qty=Decimal("1.000"),
    )
    StockItem.objects.create(
        ingredient=ingredient,
        balance_qty=Decimal("5.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    batch = create_batch_for_date(
        production_date=production_date,
        items_payload=[
            {
                "menu_item": menu_item,
                "qty_planned": 4,
                "qty_produced": 2,
            }
        ],
    )

    complete_batch(batch_id=batch.id)
    complete_batch(batch_id=batch.id)

    assert (
        StockMovement.objects.filter(
            movement_type=StockMovementType.OUT,
            reference_type=StockReferenceType.PRODUCTION,
            reference_id=batch.id,
        ).count()
        == 1
    )

    stock_item = StockItem.objects.get(ingredient=ingredient)
    assert stock_item.balance_qty == Decimal("3.000")

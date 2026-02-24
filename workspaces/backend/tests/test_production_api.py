import json
from datetime import date
from decimal import Decimal

import pytest

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.inventory.models import StockItem, StockMovement, StockReferenceType


def _create_menu_item_for_api(menu_date: date) -> tuple[MenuItem, Ingredient]:
    ingredient = Ingredient.objects.create(
        name="Ingrediente Producao API",
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name="Prato Producao API", yield_portions=10)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
    )
    menu_day = MenuDay.objects.create(
        menu_date=menu_date,
        title="Cardapio API Producao",
    )
    menu_item = MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("25.00"),
        is_active=True,
    )
    return menu_item, ingredient


@pytest.mark.django_db
def test_production_complete_endpoint_cria_movimento_e_eh_idempotente(client):
    production_date = date(2026, 3, 20)
    menu_item, ingredient = _create_menu_item_for_api(production_date)
    StockItem.objects.create(
        ingredient=ingredient,
        balance_qty=Decimal("6.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    create_payload = {
        "production_date": production_date.isoformat(),
        "note": "Lote API",
        "items": [
            {
                "menu_item": menu_item.id,
                "qty_planned": 4,
                "qty_produced": 2,
                "qty_waste": 0,
            }
        ],
    }

    create_response = client.post(
        "/api/v1/production/batches/",
        data=json.dumps(create_payload),
        content_type="application/json",
    )

    assert create_response.status_code == 201
    create_body = create_response.json()
    assert create_body["status"] == "PLANNED"
    assert len(create_body["production_items"]) == 1

    batch_id = create_body["id"]

    complete_response = client.post(f"/api/v1/production/batches/{batch_id}/complete/")
    assert complete_response.status_code == 200
    complete_body = complete_response.json()
    assert complete_body["status"] == "DONE"

    assert (
        StockMovement.objects.filter(
            reference_type=StockReferenceType.PRODUCTION,
            reference_id=batch_id,
        ).count()
        == 1
    )

    stock_item = StockItem.objects.get(ingredient=ingredient)
    assert stock_item.balance_qty == Decimal("4.000")

    complete_again_response = client.post(
        f"/api/v1/production/batches/{batch_id}/complete/"
    )
    assert complete_again_response.status_code == 200

    assert (
        StockMovement.objects.filter(
            reference_type=StockReferenceType.PRODUCTION,
            reference_id=batch_id,
        ).count()
        == 1
    )

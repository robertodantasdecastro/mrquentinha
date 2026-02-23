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


def _create_menu_item_for_api(menu_date: date) -> MenuItem:
    ingredient = Ingredient.objects.create(
        name="Ingrediente API",
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name="Prato API", yield_portions=10)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
    )
    menu_day = MenuDay.objects.create(menu_date=menu_date, title="Cardapio API")
    return MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("19.90"),
        is_active=True,
    )


@pytest.mark.django_db
def test_orders_create_endpoint_retorna_json_esperado(client):
    delivery_date = date(2026, 3, 9)
    menu_item = _create_menu_item_for_api(delivery_date)

    payload = {
        "delivery_date": delivery_date.isoformat(),
        "items": [
            {
                "menu_item": menu_item.id,
                "qty": 2,
            }
        ],
    }

    response = client.post(
        "/api/v1/orders/orders/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201

    body = response.json()
    assert body["delivery_date"] == delivery_date.isoformat()
    assert body["status"] == "CREATED"
    assert body["total_amount"] == "39.80"
    assert len(body["order_items"]) == 1
    assert body["order_items"][0]["menu_item"] == menu_item.id
    assert body["order_items"][0]["qty"] == 2
    assert body["order_items"][0]["unit_price"] == "19.90"
    assert len(body["payments"]) == 1
    assert body["payments"][0]["status"] == "PENDING"
    assert body["payments"][0]["amount"] == "39.80"

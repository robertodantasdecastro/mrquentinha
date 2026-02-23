import json

import pytest

from apps.catalog.models import Ingredient, IngredientUnit
from apps.inventory.models import StockMovement, StockMovementType


@pytest.mark.django_db
def test_inventory_movement_endpoint_integra_com_stock_item(client):
    ingredient = Ingredient.objects.create(name="batata", unit=IngredientUnit.KILOGRAM)

    payload = {
        "ingredient": ingredient.id,
        "movement_type": "IN",
        "qty": "2.500",
        "unit": "kg",
        "reference_type": "ADJUSTMENT",
        "note": "Entrada inicial",
    }

    response = client.post(
        "/api/v1/inventory/movements/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["movement_type"] == "IN"
    assert body["reference_type"] == "ADJUSTMENT"

    stock_response = client.get("/api/v1/inventory/stock-items/")
    assert stock_response.status_code == 200

    stocks = stock_response.json()
    assert len(stocks) == 1
    assert stocks[0]["ingredient"] == ingredient.id
    assert stocks[0]["balance_qty"] == "2.500"

    assert StockMovement.objects.filter(
        ingredient=ingredient,
        movement_type=StockMovementType.IN,
    ).exists()

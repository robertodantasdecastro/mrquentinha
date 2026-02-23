import json
from decimal import Decimal

import pytest

from apps.catalog.models import Ingredient, IngredientUnit
from apps.inventory.selectors import get_stock_by_ingredient


@pytest.mark.django_db
def test_procurement_request_endpoint_cria_solicitacao(client):
    ingredient = Ingredient.objects.create(name="alho", unit=IngredientUnit.KILOGRAM)

    payload = {
        "status": "OPEN",
        "note": "Repor ingredientes da semana",
        "items": [
            {
                "ingredient": ingredient.id,
                "required_qty": "1.500",
                "unit": "kg",
            }
        ],
    }

    response = client.post(
        "/api/v1/procurement/requests/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["status"] == "OPEN"
    assert len(body["request_items"]) == 1


@pytest.mark.django_db
def test_procurement_purchase_endpoint_cria_compra_e_atualiza_estoque(client):
    ingredient = Ingredient.objects.create(name="oleo", unit=IngredientUnit.LITER)

    payload = {
        "supplier_name": "Atacado Sul",
        "invoice_number": "NF-900",
        "purchase_date": "2026-02-25",
        "items": [
            {
                "ingredient": ingredient.id,
                "qty": "4.000",
                "unit": "l",
                "unit_price": "8.00",
                "tax_amount": "1.20",
            }
        ],
    }

    response = client.post(
        "/api/v1/procurement/purchases/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["supplier_name"] == "Atacado Sul"
    assert body["total_amount"] == "33.20"

    stock_item = get_stock_by_ingredient(ingredient)
    assert stock_item is not None
    assert stock_item.balance_qty == Decimal("4.000")

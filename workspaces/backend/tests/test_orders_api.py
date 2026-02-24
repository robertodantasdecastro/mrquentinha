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
from apps.finance.models import AccountType, CashDirection, CashMovement


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


def _extract_results(payload):
    return payload if isinstance(payload, list) else payload.get("results", [])


@pytest.mark.django_db
def test_orders_create_endpoint_retorna_json_e_gera_ar(client):
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
    order_id = body["id"]

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

    ar_response = client.get("/api/v1/finance/ar-receivables/")
    assert ar_response.status_code == 200

    ar_items = _extract_results(ar_response.json())
    ar_item = next(
        (
            item
            for item in ar_items
            if item["reference_type"] == "ORDER" and item["reference_id"] == order_id
        ),
        None,
    )

    assert ar_item is not None
    assert ar_item["status"] == "OPEN"
    assert ar_item["amount"] == "39.80"
    assert ar_item["due_date"] == delivery_date.isoformat()


@pytest.mark.django_db
def test_orders_payment_patch_para_paid_atualiza_ar_e_gera_caixa_in(client):
    delivery_date = date(2026, 3, 10)
    menu_item = _create_menu_item_for_api(delivery_date)

    create_response = client.post(
        "/api/v1/orders/orders/",
        data=json.dumps(
            {
                "delivery_date": delivery_date.isoformat(),
                "items": [{"menu_item": menu_item.id, "qty": 1}],
            }
        ),
        content_type="application/json",
    )
    assert create_response.status_code == 201

    order_body = create_response.json()
    payment_id = order_body["payments"][0]["id"]

    patch_response = client.patch(
        f"/api/v1/orders/payments/{payment_id}/",
        data=json.dumps({"status": "PAID", "provider_ref": "pix-api-001"}),
        content_type="application/json",
    )
    assert patch_response.status_code == 200
    patch_body = patch_response.json()
    assert patch_body["status"] == "PAID"
    assert patch_body["provider_ref"] == "pix-api-001"
    assert patch_body["paid_at"] is not None

    ar_response = client.get("/api/v1/finance/ar-receivables/")
    assert ar_response.status_code == 200

    ar_items = _extract_results(ar_response.json())
    ar_item = next(
        (
            item
            for item in ar_items
            if item["reference_type"] == "ORDER"
            and item["reference_id"] == order_body["id"]
        ),
        None,
    )

    assert ar_item is not None
    assert ar_item["status"] == "RECEIVED"

    cash_response = client.get("/api/v1/finance/cash-movements/")
    assert cash_response.status_code == 200

    cash_items = _extract_results(cash_response.json())
    cash_item = next(
        (
            item
            for item in cash_items
            if item["direction"] == "IN"
            and item["reference_type"] == "AR"
            and item["reference_id"] == ar_item["id"]
        ),
        None,
    )

    assert cash_item is not None
    assert cash_item["amount"] == order_body["total_amount"]

    patch_again_response = client.patch(
        f"/api/v1/orders/payments/{payment_id}/",
        data=json.dumps({"status": "PAID"}),
        content_type="application/json",
    )
    assert patch_again_response.status_code == 200

    movements = CashMovement.objects.filter(
        direction=CashDirection.IN,
        reference_type="AR",
        reference_id=ar_item["id"],
    )
    assert movements.count() == 1

    movement = movements.get()
    assert movement.account.name == "Caixa/Banco"
    assert movement.account.type == AccountType.ASSET

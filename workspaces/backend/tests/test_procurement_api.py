import json
from datetime import date
from decimal import Decimal
from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.finance.models import APBill
from apps.inventory.selectors import get_stock_by_ingredient
from apps.procurement.models import PurchaseRequest


def build_test_image(*, filename: str = "label.png") -> SimpleUploadedFile:
    from PIL import Image

    image = Image.new("RGB", (32, 32), color=(245, 245, 245))
    buffer = BytesIO()
    image.save(buffer, format="PNG")

    return SimpleUploadedFile(
        filename,
        buffer.getvalue(),
        content_type="image/png",
    )


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
def test_procurement_purchase_endpoint_cria_compra_ap_e_atualiza_estoque(client):
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

    purchase_id = body["id"]

    stock_item = get_stock_by_ingredient(ingredient)
    assert stock_item is not None
    assert stock_item.balance_qty == Decimal("4.000")

    assert (
        APBill.objects.filter(
            reference_type="PURCHASE",
            reference_id=purchase_id,
        ).count()
        == 1
    )

    ap_response = client.get("/api/v1/finance/ap-bills/")
    assert ap_response.status_code == 200

    ap_payload = ap_response.json()
    ap_items = (
        ap_payload if isinstance(ap_payload, list) else ap_payload.get("results", [])
    )

    assert any(
        item["reference_type"] == "PURCHASE"
        and item["reference_id"] == purchase_id
        and item["supplier_name"] == "Atacado Sul"
        and item["amount"] == "33.20"
        for item in ap_items
    )


@pytest.mark.django_db
def test_procurement_request_from_menu_endpoint_gera_purchase_request(client):
    ingredient = Ingredient.objects.create(name="tomate", unit=IngredientUnit.KILOGRAM)
    dish = Dish.objects.create(name="Molho de Tomate", yield_portions=10)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("1.500"),
        unit=IngredientUnit.KILOGRAM,
    )
    menu_day = MenuDay.objects.create(menu_date=date(2026, 3, 3), title="Cardapio")
    MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("19.90"),
        available_qty=2,
        is_active=True,
    )

    response = client.post(
        "/api/v1/procurement/requests/from-menu/",
        data=json.dumps({"menu_day_id": menu_day.id}),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["created"] is True
    assert body["purchase_request_id"] is not None
    assert body["message"] == "purchase request gerada"
    assert len(body["items"]) == 1
    assert body["items"][0]["ingredient_id"] == ingredient.id
    assert body["items"][0]["required_qty"] == "3.000"

    purchase_request = PurchaseRequest.objects.get(pk=body["purchase_request_id"])
    assert purchase_request.items.count() == 1
    assert purchase_request.items.first().required_qty == Decimal("3.000")


@pytest.mark.django_db
def test_procurement_purchase_item_label_image_endpoint_salva_arquivo(client):
    ingredient = Ingredient.objects.create(name="cenoura", unit=IngredientUnit.KILOGRAM)

    payload = {
        "supplier_name": "Fornecedor Foto",
        "purchase_date": "2026-02-26",
        "items": [
            {
                "ingredient": ingredient.id,
                "qty": "2.000",
                "unit": "kg",
                "unit_price": "5.00",
            }
        ],
    }

    create_response = client.post(
        "/api/v1/procurement/purchases/",
        data=json.dumps(payload),
        content_type="application/json",
    )
    assert create_response.status_code == 201

    purchase_body = create_response.json()
    purchase_id = purchase_body["id"]
    purchase_item_id = purchase_body["purchase_items"][0]["id"]

    upload_response = client.post(
        f"/api/v1/procurement/purchases/{purchase_id}/items/{purchase_item_id}/label-image/",
        data={
            "side": "front",
            "label_image": build_test_image(),
        },
    )

    assert upload_response.status_code == 200
    upload_body = upload_response.json()
    assert upload_body["id"] == purchase_item_id
    assert upload_body["label_front_image_url"] is not None

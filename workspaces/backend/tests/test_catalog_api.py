import json
from decimal import Decimal

import pytest

from apps.catalog.models import Ingredient, IngredientUnit
from apps.catalog.services import create_dish_with_ingredients


@pytest.mark.django_db
def test_post_ingredient_endpoint_cria_registro(client):
    payload = {
        "name": "  Cebola Roxa  ",
        "unit": IngredientUnit.KILOGRAM,
        "is_active": True,
    }

    response = client.post(
        "/api/v1/catalog/ingredients/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "cebola roxa"
    assert body["unit"] == IngredientUnit.KILOGRAM


@pytest.mark.django_db
def test_cria_menu_e_consulta_por_data_endpoint(client):
    frango = Ingredient.objects.create(name="frango", unit=IngredientUnit.KILOGRAM)
    batata = Ingredient.objects.create(name="batata", unit=IngredientUnit.KILOGRAM)

    prato_ativo = create_dish_with_ingredients(
        dish_data={
            "name": "Frango Grelhado",
            "description": "Proteina",
            "yield_portions": 10,
        },
        ingredients_payload=[
            {
                "ingredient": frango,
                "quantity": Decimal("1.500"),
                "unit": "kg",
            }
        ],
    )
    prato_inativo = create_dish_with_ingredients(
        dish_data={
            "name": "Batata Saute",
            "description": "Acompanhamento",
            "yield_portions": 10,
        },
        ingredients_payload=[
            {
                "ingredient": batata,
                "quantity": Decimal("1.100"),
                "unit": "kg",
            }
        ],
    )

    menu_payload = {
        "menu_date": "2026-02-24",
        "title": "Cardapio de Terca",
        "items": [
            {
                "dish": prato_ativo.id,
                "sale_price": "24.90",
                "available_qty": 30,
                "is_active": True,
            },
            {
                "dish": prato_inativo.id,
                "sale_price": "18.90",
                "available_qty": 10,
                "is_active": False,
            },
        ],
    }

    create_response = client.post(
        "/api/v1/catalog/menus/",
        data=json.dumps(menu_payload),
        content_type="application/json",
    )

    assert create_response.status_code == 201

    by_date_response = client.get("/api/v1/catalog/menus/by-date/2026-02-24/")

    assert by_date_response.status_code == 200
    body = by_date_response.json()
    assert body["menu_date"] == "2026-02-24"
    assert body["title"] == "Cardapio de Terca"
    assert len(body["menu_items"]) == 1
    assert body["menu_items"][0]["dish"]["name"] == "Frango Grelhado"
    assert len(body["menu_items"][0]["dish"]["composition"]) == 1
    ingredient_payload = body["menu_items"][0]["dish"]["composition"][0]["ingredient"]
    assert ingredient_payload["name"] == "frango"
    assert "image_url" in body["menu_items"][0]["dish"]["composition"][0]["ingredient"]


@pytest.mark.django_db
def test_post_dish_endpoint_cria_prato_com_composicao(client):
    arroz = Ingredient.objects.create(name="arroz", unit=IngredientUnit.KILOGRAM)

    payload = {
        "name": "Arroz Branco",
        "description": "Guarnicao",
        "yield_portions": 12,
        "ingredients": [
            {
                "ingredient": arroz.id,
                "quantity": "1.000",
                "unit": "kg",
            }
        ],
    }

    response = client.post(
        "/api/v1/catalog/dishes/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Arroz Branco"
    assert len(body["composition"]) == 1
    assert body["composition"][0]["ingredient"]["name"] == "arroz"

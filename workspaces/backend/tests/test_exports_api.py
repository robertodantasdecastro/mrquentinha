from datetime import date
from decimal import Decimal

import pytest

from apps.accounts.services import SystemRole
from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.orders.services import create_order, update_payment_status
from apps.procurement.services import create_purchase_and_apply_stock
from apps.production.services import create_batch_for_date


def _create_menu_item(
    *, menu_date: date, dish_name: str, ingredient_name: str
) -> MenuItem:
    ingredient = Ingredient.objects.create(
        name=ingredient_name,
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name=dish_name, yield_portions=10)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("1.000"),
        unit=IngredientUnit.KILOGRAM,
    )
    menu_day = MenuDay.objects.create(menu_date=menu_date, title="Cardapio Export")
    return MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("18.90"),
        is_active=True,
    )


def _csv_lines(response) -> list[str]:
    return response.content.decode("utf-8").strip().splitlines()


@pytest.mark.django_db
def test_export_pedidos_csv_retorna_header_em_pt_br(client, create_user_with_roles):
    delivery_date = date(2026, 3, 20)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        dish_name="Prato Export Pedido",
        ingredient_name="Ingrediente Export Pedido",
    )

    customer = create_user_with_roles(
        username="customer_export_orders", role_codes=[SystemRole.CLIENTE]
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
        payment_method="PIX",
    )
    payment = order.payments.first()
    update_payment_status(
        payment_id=payment.id,
        update_data={"status": "PAID", "provider_ref": "export-001"},
        actor_user=None,
    )

    response = client.get(
        "/api/v1/orders/reports/orders/?from=2026-03-01&to=2026-03-31"
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "pedidos_2026-03-01_2026-03-31.csv" in response["Content-Disposition"]

    lines = _csv_lines(response)
    assert lines[0].startswith(
        "pedido_id,data_entrega,status,valor_total,cliente_id,cliente_nome,metodos_pagamento,total_pago"
    )
    assert str(order.id) in lines[1]


@pytest.mark.django_db
def test_export_compras_csv_retorna_itens_em_pt_br(client):
    ingredient = Ingredient.objects.create(
        name="Ingrediente Export Compra",
        unit=IngredientUnit.KILOGRAM,
    )
    create_purchase_and_apply_stock(
        purchase_data={
            "supplier_name": "Fornecedor Export",
            "invoice_number": "NF-EXP-01",
            "purchase_date": date(2026, 3, 5),
        },
        items_payload=[
            {
                "ingredient": ingredient,
                "qty": Decimal("5.000"),
                "unit": IngredientUnit.KILOGRAM,
                "unit_price": Decimal("12.50"),
                "tax_amount": Decimal("1.50"),
            }
        ],
    )

    response = client.get(
        "/api/v1/procurement/reports/purchases/?from=2026-03-01&to=2026-03-31"
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "compras_2026-03-01_2026-03-31.csv" in response["Content-Disposition"]

    lines = _csv_lines(response)
    assert lines[0].startswith(
        "compra_id,data_compra,fornecedor,nota_fiscal,ingrediente,quantidade,unidade,preco_unitario,imposto,total_item,total_compra"
    )
    assert "Fornecedor Export" in lines[1]


@pytest.mark.django_db
def test_export_producao_csv_retorna_lotes(client):
    production_date = date(2026, 3, 8)
    menu_item = _create_menu_item(
        menu_date=production_date,
        dish_name="Prato Export Producao",
        ingredient_name="Ingrediente Export Producao",
    )

    batch = create_batch_for_date(
        production_date=production_date,
        items_payload=[
            {
                "menu_item": menu_item,
                "qty_planned": 10,
                "qty_produced": 8,
                "qty_waste": 1,
            }
        ],
    )

    response = client.get(
        "/api/v1/production/reports/production/?from=2026-03-01&to=2026-03-31"
    )

    assert response.status_code == 200
    assert response["Content-Type"].startswith("text/csv")
    assert "producao_2026-03-01_2026-03-31.csv" in response["Content-Disposition"]

    lines = _csv_lines(response)
    assert lines[0].startswith(
        "lote_id,data_producao,status,prato,quantidade_planejada,quantidade_produzida,quantidade_perdas"
    )
    assert str(batch.id) in lines[1]


@pytest.mark.django_db
def test_export_financeiro_csv_fluxo_caixa_e_dre(client, create_user_with_roles):
    delivery_date = date(2026, 3, 22)
    menu_item = _create_menu_item(
        menu_date=delivery_date,
        dish_name="Prato Export Finance",
        ingredient_name="Ingrediente Export Finance",
    )

    customer = create_user_with_roles(
        username="customer_export_finance", role_codes=[SystemRole.CLIENTE]
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
        payment_method="PIX",
    )
    payment = order.payments.first()
    update_payment_status(
        payment_id=payment.id,
        update_data={"status": "PAID", "provider_ref": "export-002"},
        actor_user=None,
    )

    cashflow_response = client.get(
        "/api/v1/finance/reports/cashflow/export/?from=2026-03-01&to=2026-03-31"
    )
    assert cashflow_response.status_code == 200
    assert cashflow_response["Content-Type"].startswith("text/csv")
    assert (
        "fluxo_caixa_2026-03-01_2026-03-31.csv"
        in cashflow_response["Content-Disposition"]
    )
    cashflow_lines = _csv_lines(cashflow_response)
    assert cashflow_lines[0].startswith(
        "data,total_entradas,total_saidas,saldo_dia,saldo_acumulado"
    )

    dre_response = client.get(
        "/api/v1/finance/reports/dre/export/?from=2026-03-01&to=2026-03-31"
    )
    assert dre_response.status_code == 200
    assert dre_response["Content-Type"].startswith("text/csv")
    assert "dre_2026-03-01_2026-03-31.csv" in dre_response["Content-Disposition"]
    dre_lines = _csv_lines(dre_response)
    assert dre_lines[0] == "indicador,valor"
    assert "receita_total" in dre_lines[1]

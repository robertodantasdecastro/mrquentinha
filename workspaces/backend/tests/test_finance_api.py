import json
from datetime import date, datetime
from decimal import Decimal

import pytest
from django.utils import timezone

from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.finance.models import (
    Account,
    AccountType,
    APBill,
    APBillStatus,
    CashDirection,
    CashMovement,
)
from apps.orders.models import Order, OrderItem, OrderStatus
from apps.procurement.models import Purchase, PurchaseItem


def _setup_reports_scenario() -> tuple[str, str]:
    period_from = "2026-04-01"
    period_to = "2026-04-30"

    ingredient = Ingredient.objects.create(
        name="Ingrediente API DRE",
        unit=IngredientUnit.KILOGRAM,
    )
    dish = Dish.objects.create(name="Prato API DRE", yield_portions=2)
    DishIngredient.objects.create(
        dish=dish,
        ingredient=ingredient,
        quantity=Decimal("2.000"),
        unit=IngredientUnit.KILOGRAM,
    )

    menu_day = MenuDay.objects.create(
        menu_date=date(2026, 4, 20),
        title="Cardapio API DRE",
    )
    menu_item = MenuItem.objects.create(
        menu_day=menu_day,
        dish=dish,
        sale_price=Decimal("10.00"),
        is_active=True,
    )

    purchase = Purchase.objects.create(
        supplier_name="Fornecedor API DRE",
        purchase_date=date(2026, 4, 10),
        total_amount=Decimal("60.00"),
    )
    PurchaseItem.objects.create(
        purchase=purchase,
        ingredient=ingredient,
        qty=Decimal("10.000"),
        unit=IngredientUnit.KILOGRAM,
        unit_price=Decimal("6.00"),
        tax_amount=Decimal("0.00"),
    )

    order = Order.objects.create(
        customer=None,
        delivery_date=date(2026, 4, 20),
        status=OrderStatus.DELIVERED,
        total_amount=Decimal("30.00"),
    )
    OrderItem.objects.create(
        order=order,
        menu_item=menu_item,
        qty=3,
        unit_price=Decimal("10.00"),
    )

    expense_account = Account.objects.create(
        name="Conta Despesa API DRE",
        type=AccountType.EXPENSE,
    )
    APBill.objects.create(
        supplier_name="Fornecedor Despesa API DRE",
        account=expense_account,
        amount=Decimal("5.00"),
        due_date=date(2026, 4, 22),
        status=APBillStatus.PAID,
        paid_at=timezone.make_aware(datetime(2026, 4, 22, 10, 0)),
    )

    return period_from, period_to


@pytest.mark.django_db
def test_finance_accounts_endpoint_cria_conta(client):
    payload = {
        "name": "Conta API",
        "type": "REVENUE",
        "is_active": True,
    }

    response = client.post(
        "/api/v1/finance/accounts/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["name"] == "Conta API"
    assert body["type"] == "REVENUE"


@pytest.mark.django_db
def test_finance_ap_bills_endpoint_cria_titulo(client):
    account_response = client.post(
        "/api/v1/finance/accounts/",
        data=json.dumps(
            {
                "name": "Conta AP",
                "type": "EXPENSE",
                "is_active": True,
            }
        ),
        content_type="application/json",
    )
    assert account_response.status_code == 201

    payload = {
        "supplier_name": "Fornecedor API",
        "account": account_response.json()["id"],
        "amount": "90.30",
        "due_date": "2026-03-20",
        "status": "OPEN",
        "reference_type": "PURCHASE",
        "reference_id": 1001,
    }

    response = client.post(
        "/api/v1/finance/ap-bills/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["supplier_name"] == "Fornecedor API"
    assert body["reference_type"] == "PURCHASE"
    assert body["reference_id"] == 1001


@pytest.mark.django_db
def test_finance_ar_receivables_endpoint_cria_titulo(client):
    account_response = client.post(
        "/api/v1/finance/accounts/",
        data=json.dumps(
            {
                "name": "Conta AR",
                "type": "REVENUE",
                "is_active": True,
            }
        ),
        content_type="application/json",
    )
    assert account_response.status_code == 201

    payload = {
        "customer": None,
        "account": account_response.json()["id"],
        "amount": "120.00",
        "due_date": "2026-03-21",
        "status": "OPEN",
        "reference_type": "ORDER",
        "reference_id": 2001,
    }

    response = client.post(
        "/api/v1/finance/ar-receivables/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["amount"] == "120.00"
    assert body["reference_type"] == "ORDER"
    assert body["reference_id"] == 2001


@pytest.mark.django_db
def test_finance_cash_movements_endpoint_cria_movimento(client):
    account_response = client.post(
        "/api/v1/finance/accounts/",
        data=json.dumps(
            {
                "name": "Conta Caixa",
                "type": "ASSET",
                "is_active": True,
            }
        ),
        content_type="application/json",
    )
    assert account_response.status_code == 201

    payload = {
        "direction": "IN",
        "amount": "45.90",
        "account": account_response.json()["id"],
        "note": "Entrada API",
        "reference_type": "PAYMENT",
        "reference_id": 3001,
    }

    response = client.post(
        "/api/v1/finance/cash-movements/",
        data=json.dumps(payload),
        content_type="application/json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["direction"] == "IN"
    assert body["amount"] == "45.90"
    assert body["reference_type"] == "PAYMENT"
    assert body["reference_id"] == 3001


@pytest.mark.django_db
def test_finance_cashflow_report_endpoint_agrega_por_dia(client):
    cash_account = Account.objects.create(
        name="Conta Caixa API", type=AccountType.ASSET
    )

    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 5, 8, 0)),
        direction=CashDirection.IN,
        amount="100.00",
        account=cash_account,
        reference_type="AR",
        reference_id=101,
    )
    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 5, 13, 0)),
        direction=CashDirection.OUT,
        amount="30.00",
        account=cash_account,
        reference_type="AP",
        reference_id=201,
    )
    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 3, 6, 9, 0)),
        direction=CashDirection.IN,
        amount="50.00",
        account=cash_account,
        reference_type="AR",
        reference_id=102,
    )

    response = client.get(
        "/api/v1/finance/reports/cashflow/?from=2026-03-05&to=2026-03-06"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["from"] == "2026-03-05"
    assert body["to"] == "2026-03-06"
    assert len(body["items"]) == 2

    assert body["items"][0] == {
        "date": "2026-03-05",
        "total_in": "100.00",
        "total_out": "30.00",
        "net": "70.00",
        "running_balance": "70.00",
    }
    assert body["items"][1] == {
        "date": "2026-03-06",
        "total_in": "50.00",
        "total_out": "0.00",
        "net": "50.00",
        "running_balance": "120.00",
    }


@pytest.mark.django_db
def test_finance_dre_report_endpoint_retorna_200_com_dados_consistentes(client):
    period_from, period_to = _setup_reports_scenario()

    response = client.get(
        f"/api/v1/finance/reports/dre/?from={period_from}&to={period_to}"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["from"] == period_from
    assert body["to"] == period_to
    assert body["dre"] == {
        "receita_total": "30.00",
        "despesas_total": "5.00",
        "cmv_estimado": "18.00",
        "lucro_bruto": "12.00",
        "resultado": "7.00",
    }


@pytest.mark.django_db
def test_finance_kpis_report_endpoint_retorna_200_com_kpis_basicos(client):
    period_from, period_to = _setup_reports_scenario()

    response = client.get(
        f"/api/v1/finance/reports/kpis/?from={period_from}&to={period_to}"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["from"] == period_from
    assert body["to"] == period_to
    assert body["kpis"] == {
        "pedidos": 1,
        "receita_total": "30.00",
        "despesas_total": "5.00",
        "cmv_estimado": "18.00",
        "lucro_bruto": "12.00",
        "ticket_medio": "30.00",
        "margem_media": "40.00",
    }


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/finance/reports/cashflow/",
        "/api/v1/finance/reports/dre/",
        "/api/v1/finance/reports/kpis/",
    ],
)
def test_finance_reports_endpoint_exige_from_e_to(client, endpoint):
    response = client.get(endpoint)

    assert response.status_code == 400
    assert "obrigatorios" in response.json()["detail"]


@pytest.mark.django_db
@pytest.mark.parametrize(
    "endpoint",
    [
        "/api/v1/finance/reports/cashflow/",
        "/api/v1/finance/reports/dre/",
        "/api/v1/finance/reports/kpis/",
    ],
)
def test_finance_reports_endpoint_valida_intervalo(client, endpoint):
    response = client.get(f"{endpoint}?from=2026-03-10&to=2026-03-09")

    assert response.status_code == 400
    assert "menor ou igual" in response.json()["detail"]

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
    BankStatement,
    CashDirection,
    CashMovement,
    LedgerEntry,
    StatementLine,
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
def test_finance_ledger_endpoint_lista_entries(client):
    debit_account = Account.objects.create(
        name="Conta Debito Ledger API",
        type=AccountType.EXPENSE,
    )
    credit_account = Account.objects.create(
        name="Conta Credito Ledger API",
        type=AccountType.ASSET,
    )

    entry = LedgerEntry.objects.create(
        entry_type="CASH_OUT",
        amount=Decimal("33.40"),
        debit_account=debit_account,
        credit_account=credit_account,
        reference_type="AP",
        reference_id=999,
        note="Teste ledger API",
    )

    response = client.get("/api/v1/finance/ledger/")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    item = body[0]
    assert item["id"] == entry.id
    assert item["entry_type"] == "CASH_OUT"
    assert item["amount"] == "33.40"
    assert item["reference_type"] == "AP"
    assert item["reference_id"] == 999


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
        "/api/v1/finance/reports/unreconciled/",
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
        "/api/v1/finance/reports/unreconciled/",
    ],
)
def test_finance_reports_endpoint_valida_intervalo(client, endpoint):
    response = client.get(f"{endpoint}?from=2026-03-10&to=2026-03-09")

    assert response.status_code == 400
    assert "menor ou igual" in response.json()["detail"]


@pytest.mark.django_db
def test_finance_bank_statement_e_lines_endpoints_criam_dados(client):
    statement_payload = {
        "period_start": "2026-08-01",
        "period_end": "2026-08-31",
        "opening_balance": "1000.00",
        "closing_balance": "1200.00",
        "source": "Banco MVP",
    }

    statement_response = client.post(
        "/api/v1/finance/bank-statements/",
        data=json.dumps(statement_payload),
        content_type="application/json",
    )

    assert statement_response.status_code == 201
    statement_id = statement_response.json()["id"]

    line_response = client.post(
        f"/api/v1/finance/bank-statements/{statement_id}/lines/",
        data=json.dumps(
            {
                "line_date": "2026-08-05",
                "description": "Credito PIX",
                "amount": "150.00",
            }
        ),
        content_type="application/json",
    )

    assert line_response.status_code == 201
    assert line_response.json()["statement"] == statement_id

    list_lines_response = client.get(
        f"/api/v1/finance/bank-statements/{statement_id}/lines/"
    )

    assert list_lines_response.status_code == 200
    assert len(list_lines_response.json()) == 1


@pytest.mark.django_db
def test_finance_cash_movement_reconcile_e_unreconcile_endpoints(client):
    cash_account = Account.objects.create(
        name="Conta Caixa API Rec", type=AccountType.ASSET
    )
    movement = CashMovement.objects.create(
        direction=CashDirection.IN,
        amount=Decimal("99.90"),
        account=cash_account,
        reference_type="AR",
        reference_id=987,
    )
    statement = BankStatement.objects.create(
        period_start=date(2026, 9, 1),
        period_end=date(2026, 9, 30),
    )
    line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 9, 10),
        description="Recebimento no banco",
        amount=Decimal("99.90"),
    )

    reconcile_response = client.post(
        f"/api/v1/finance/cash-movements/{movement.id}/reconcile/",
        data=json.dumps({"statement_line_id": line.id}),
        content_type="application/json",
    )

    assert reconcile_response.status_code == 200
    reconcile_body = reconcile_response.json()
    assert reconcile_body["is_reconciled"] is True
    assert reconcile_body["statement_line"] == line.id

    unreconcile_response = client.post(
        f"/api/v1/finance/cash-movements/{movement.id}/unreconcile/",
        data=json.dumps({}),
        content_type="application/json",
    )

    assert unreconcile_response.status_code == 200
    unreconcile_body = unreconcile_response.json()
    assert unreconcile_body["is_reconciled"] is False
    assert unreconcile_body["statement_line"] is None


@pytest.mark.django_db
def test_finance_unreconciled_report_retorna_apenas_pendentes(client):
    cash_account = Account.objects.create(
        name="Conta Caixa API Pend", type=AccountType.ASSET
    )
    pending = CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 10, 10, 10, 0)),
        direction=CashDirection.IN,
        amount=Decimal("120.00"),
        account=cash_account,
        reference_type="AR",
        reference_id=1001,
        is_reconciled=False,
    )

    statement = BankStatement.objects.create(
        period_start=date(2026, 10, 1),
        period_end=date(2026, 10, 31),
    )
    line = StatementLine.objects.create(
        statement=statement,
        line_date=date(2026, 10, 11),
        description="Linha conciliada",
        amount=Decimal("80.00"),
    )
    CashMovement.objects.create(
        movement_date=timezone.make_aware(datetime(2026, 10, 11, 9, 0)),
        direction=CashDirection.OUT,
        amount=Decimal("80.00"),
        account=cash_account,
        reference_type="AP",
        reference_id=1002,
        statement_line=line,
        is_reconciled=True,
    )

    response = client.get(
        "/api/v1/finance/reports/unreconciled/?from=2026-10-01&to=2026-10-31"
    )

    assert response.status_code == 200
    body = response.json()
    assert body["from"] == "2026-10-01"
    assert body["to"] == "2026-10-31"
    assert len(body["items"]) == 1
    assert body["items"][0]["id"] == pending.id
    assert body["items"][0]["is_reconciled"] is False

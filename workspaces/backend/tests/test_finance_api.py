import json
from datetime import datetime

import pytest
from django.utils import timezone

from apps.finance.models import Account, AccountType, CashDirection, CashMovement


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
def test_finance_cashflow_report_endpoint_exige_from_e_to(client):
    response = client.get("/api/v1/finance/reports/cashflow/")

    assert response.status_code == 400
    assert "obrigatorios" in response.json()["detail"]


@pytest.mark.django_db
def test_finance_cashflow_report_endpoint_valida_intervalo(client):
    response = client.get(
        "/api/v1/finance/reports/cashflow/?from=2026-03-10&to=2026-03-09"
    )

    assert response.status_code == 400
    assert "menor ou igual" in response.json()["detail"]

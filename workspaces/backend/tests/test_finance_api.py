import json

import pytest


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

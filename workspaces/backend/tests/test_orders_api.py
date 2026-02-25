import json
from datetime import date
from decimal import Decimal

import pytest
from rest_framework.test import APIClient

from apps.accounts.services import SystemRole
from apps.catalog.models import (
    Dish,
    DishIngredient,
    Ingredient,
    IngredientUnit,
    MenuDay,
    MenuItem,
)
from apps.finance.models import AccountType, CashDirection, CashMovement
from apps.orders.models import PaymentWebhookEvent
from apps.orders.services import create_order


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


def _auth_client(user):
    api_client = APIClient()
    api_client.force_authenticate(user=user)
    return api_client


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


@pytest.mark.django_db
def test_orders_list_filtra_por_usuario_e_admin_lista_todos(
    create_user_with_roles, admin_user
):
    delivery_date = date(2026, 3, 11)
    menu_item = _create_menu_item_for_api(delivery_date)

    user_a = create_user_with_roles(
        username="cliente_a", role_codes=[SystemRole.CLIENTE]
    )
    user_b = create_user_with_roles(
        username="cliente_b", role_codes=[SystemRole.CLIENTE]
    )

    order_a = create_order(
        customer=user_a,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    order_b = create_order(
        customer=user_b,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )

    client_a = _auth_client(user_a)
    response_a = client_a.get("/api/v1/orders/orders/")
    assert response_a.status_code == 200
    ids_a = {item["id"] for item in _extract_results(response_a.json())}
    assert ids_a == {order_a.id}

    client_b = _auth_client(user_b)
    response_b = client_b.get("/api/v1/orders/orders/")
    assert response_b.status_code == 200
    ids_b = {item["id"] for item in _extract_results(response_b.json())}
    assert ids_b == {order_b.id}

    admin_client = _auth_client(admin_user)
    response_admin = admin_client.get("/api/v1/orders/orders/")
    assert response_admin.status_code == 200
    ids_admin = {item["id"] for item in _extract_results(response_admin.json())}
    assert {order_a.id, order_b.id}.issubset(ids_admin)


@pytest.mark.django_db
def test_cliente_nao_altera_status_ou_pagamento_de_outro_cliente(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 12)
    menu_item = _create_menu_item_for_api(delivery_date)

    owner = create_user_with_roles(
        username="cliente_owner", role_codes=[SystemRole.CLIENTE]
    )
    other = create_user_with_roles(
        username="cliente_other", role_codes=[SystemRole.CLIENTE]
    )

    order_owner = create_order(
        customer=owner,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment_owner = order_owner.payments.get()

    other_client = _auth_client(other)

    status_response = other_client.patch(
        f"/api/v1/orders/orders/{order_owner.id}/status/",
        data=json.dumps({"status": "CANCELED"}),
        content_type="application/json",
    )
    assert status_response.status_code == 404

    payment_response = other_client.patch(
        f"/api/v1/orders/payments/{payment_owner.id}/",
        data=json.dumps({"status": "PAID"}),
        content_type="application/json",
    )
    assert payment_response.status_code == 404


@pytest.mark.django_db
def test_financeiro_lista_todos_e_atualiza_pagamento_de_terceiro(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 17)
    menu_item = _create_menu_item_for_api(delivery_date)

    user_a = create_user_with_roles(
        username="cliente_fin_a", role_codes=[SystemRole.CLIENTE]
    )
    user_b = create_user_with_roles(
        username="cliente_fin_b", role_codes=[SystemRole.CLIENTE]
    )
    financeiro = create_user_with_roles(
        username="financeiro_api",
        role_codes=[SystemRole.FINANCEIRO],
        is_staff=False,
    )

    order_a = create_order(
        customer=user_a,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    order_b = create_order(
        customer=user_b,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )

    financeiro_client = _auth_client(financeiro)

    orders_response = financeiro_client.get("/api/v1/orders/orders/")
    assert orders_response.status_code == 200
    ids = {item["id"] for item in _extract_results(orders_response.json())}
    assert {order_a.id, order_b.id}.issubset(ids)

    payment_b = order_b.payments.get()
    payment_response = financeiro_client.patch(
        f"/api/v1/orders/payments/{payment_b.id}/",
        data=json.dumps({"status": "PAID"}),
        content_type="application/json",
    )
    assert payment_response.status_code == 200
    assert payment_response.json()["status"] == "PAID"


@pytest.mark.django_db
def test_payment_intent_post_cria_e_retry_idempotente(create_user_with_roles):
    delivery_date = date(2026, 3, 22)
    menu_item = _create_menu_item_for_api(delivery_date)

    customer = create_user_with_roles(
        username="cliente_intent_post",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    customer_client = _auth_client(customer)
    endpoint = f"/api/v1/orders/payments/{payment.id}/intent/"

    create_response = customer_client.post(
        endpoint,
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-api-001",
    )
    assert create_response.status_code == 201

    create_body = create_response.json()
    assert create_body["idempotent_replay"] is False
    assert create_body["payment_id"] == payment.id

    retry_response = customer_client.post(
        endpoint,
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-api-001",
    )
    assert retry_response.status_code == 200

    retry_body = retry_response.json()
    assert retry_body["id"] == create_body["id"]
    assert retry_body["idempotent_replay"] is True


@pytest.mark.django_db
def test_payment_intent_post_retorna_400_sem_header_idempotency_key(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 23)
    menu_item = _create_menu_item_for_api(delivery_date)

    customer = create_user_with_roles(
        username="cliente_intent_sem_header",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    customer_client = _auth_client(customer)
    response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
    )

    assert response.status_code == 400
    assert "Idempotency-Key" in str(response.json())


@pytest.mark.django_db
def test_payment_intent_post_retorna_404_para_pagamento_de_outro_cliente(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 24)
    menu_item = _create_menu_item_for_api(delivery_date)

    owner = create_user_with_roles(
        username="cliente_intent_owner",
        role_codes=[SystemRole.CLIENTE],
    )
    other = create_user_with_roles(
        username="cliente_intent_other",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=owner,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    other_client = _auth_client(other)
    response = other_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-other-001",
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_payment_intent_post_retorna_409_para_pagamento_ja_pago(create_user_with_roles):
    delivery_date = date(2026, 3, 25)
    menu_item = _create_menu_item_for_api(delivery_date)

    customer = create_user_with_roles(
        username="cliente_intent_paid",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()
    payment.status = "PAID"
    payment.save(update_fields=["status"])

    customer_client = _auth_client(customer)
    response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-paid-api-001",
    )

    assert response.status_code == 409
    assert "Pagamento ja confirmado" in response.json()["detail"]


@pytest.mark.django_db
def test_payment_intent_latest_retorna_intent_mais_recente(create_user_with_roles):
    delivery_date = date(2026, 3, 26)
    menu_item = _create_menu_item_for_api(delivery_date)

    customer = create_user_with_roles(
        username="cliente_intent_latest",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    customer_client = _auth_client(customer)
    create_response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-latest-001",
    )
    assert create_response.status_code == 201
    created_intent_id = create_response.json()["id"]

    latest_response = customer_client.get(
        f"/api/v1/orders/payments/{payment.id}/intent/latest/"
    )

    assert latest_response.status_code == 200
    assert latest_response.json()["id"] == created_intent_id


@pytest.mark.django_db
def test_payment_intent_post_retorna_409_para_chave_diferente_com_intent_ativo(
    create_user_with_roles,
):
    delivery_date = date(2026, 3, 27)
    menu_item = _create_menu_item_for_api(delivery_date)

    customer = create_user_with_roles(
        username="cliente_intent_conflict",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    customer_client = _auth_client(customer)

    first_response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-conflict-001",
    )
    assert first_response.status_code == 201

    conflict_response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-conflict-002",
    )
    assert conflict_response.status_code == 409


@pytest.mark.django_db
def test_payment_webhook_succeeded_reconcilia_pagamento_e_replay_idempotente(
    create_user_with_roles,
    client,
    settings,
):
    settings.PAYMENTS_WEBHOOK_TOKEN = "webhook-token-test"

    delivery_date = date(2026, 3, 28)
    menu_item = _create_menu_item_for_api(delivery_date)
    customer = create_user_with_roles(
        username="cliente_webhook_success",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    customer_client = _auth_client(customer)
    intent_response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-webhook-success-001",
    )
    assert intent_response.status_code == 201

    provider_intent_ref = intent_response.json()["provider_intent_ref"]
    webhook_payload = {
        "provider": "mock",
        "event_id": "evt-webhook-success-001",
        "provider_intent_ref": provider_intent_ref,
        "intent_status": "SUCCEEDED",
        "provider_ref": "provider-success-001",
    }

    webhook_client = APIClient()
    first_response = webhook_client.post(
        "/api/v1/orders/payments/webhook/",
        data=json.dumps(webhook_payload),
        content_type="application/json",
        HTTP_X_WEBHOOK_TOKEN=settings.PAYMENTS_WEBHOOK_TOKEN,
    )
    assert first_response.status_code == 201
    first_body = first_response.json()
    assert first_body["idempotent_replay"] is False
    assert first_body["payment_id"] == payment.id
    assert first_body["intent_status"] == "SUCCEEDED"
    assert first_body["payment_status"] == "PAID"

    payment.refresh_from_db()
    assert payment.status == "PAID"
    assert payment.provider_ref == "provider-success-001"

    ar_response = client.get("/api/v1/finance/ar-receivables/")
    assert ar_response.status_code == 200
    ar_items = _extract_results(ar_response.json())
    ar_item = next(
        (
            item
            for item in ar_items
            if item["reference_type"] == "ORDER" and item["reference_id"] == order.id
        ),
        None,
    )

    assert ar_item is not None
    assert ar_item["status"] == "RECEIVED"

    movements_before = CashMovement.objects.filter(
        direction=CashDirection.IN,
        reference_type="AR",
        reference_id=ar_item["id"],
    ).count()
    assert movements_before == 1

    replay_response = webhook_client.post(
        "/api/v1/orders/payments/webhook/",
        data=json.dumps(webhook_payload),
        content_type="application/json",
        HTTP_X_WEBHOOK_TOKEN=settings.PAYMENTS_WEBHOOK_TOKEN,
    )
    assert replay_response.status_code == 200
    replay_body = replay_response.json()
    assert replay_body["idempotent_replay"] is True

    assert (
        PaymentWebhookEvent.objects.filter(
            provider="mock",
            event_id="evt-webhook-success-001",
        ).count()
        == 1
    )

    movements_after = CashMovement.objects.filter(
        direction=CashDirection.IN,
        reference_type="AR",
        reference_id=ar_item["id"],
    ).count()
    assert movements_after == 1


@pytest.mark.django_db
def test_payment_webhook_retorna_401_sem_token(settings):
    settings.PAYMENTS_WEBHOOK_TOKEN = "webhook-token-required"

    webhook_client = APIClient()
    response = webhook_client.post(
        "/api/v1/orders/payments/webhook/",
        data=json.dumps({"event_id": "evt-missing-token"}),
        content_type="application/json",
    )

    assert response.status_code == 401


@pytest.mark.django_db
def test_payment_webhook_retorna_404_quando_intent_nao_encontrado(settings):
    settings.PAYMENTS_WEBHOOK_TOKEN = "webhook-token-not-found"

    webhook_client = APIClient()
    response = webhook_client.post(
        "/api/v1/orders/payments/webhook/",
        data=json.dumps(
            {
                "provider": "mock",
                "event_id": "evt-not-found-001",
                "provider_intent_ref": "intent-inexistente",
                "intent_status": "SUCCEEDED",
            }
        ),
        content_type="application/json",
        HTTP_X_WEBHOOK_TOKEN=settings.PAYMENTS_WEBHOOK_TOKEN,
    )

    assert response.status_code == 404


@pytest.mark.django_db
def test_payment_webhook_failed_marca_pagamento_failed_sem_entrada_caixa(
    create_user_with_roles,
    client,
    settings,
):
    settings.PAYMENTS_WEBHOOK_TOKEN = "webhook-token-failed"

    delivery_date = date(2026, 3, 29)
    menu_item = _create_menu_item_for_api(delivery_date)
    customer = create_user_with_roles(
        username="cliente_webhook_failed",
        role_codes=[SystemRole.CLIENTE],
    )

    order = create_order(
        customer=customer,
        delivery_date=delivery_date,
        items_payload=[{"menu_item": menu_item, "qty": 1}],
    )
    payment = order.payments.get()

    customer_client = _auth_client(customer)
    intent_response = customer_client.post(
        f"/api/v1/orders/payments/{payment.id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-webhook-failed-001",
    )
    assert intent_response.status_code == 201

    provider_intent_ref = intent_response.json()["provider_intent_ref"]

    webhook_client = APIClient()
    failed_response = webhook_client.post(
        "/api/v1/orders/payments/webhook/",
        data=json.dumps(
            {
                "provider": "mock",
                "event_id": "evt-webhook-failed-001",
                "provider_intent_ref": provider_intent_ref,
                "intent_status": "FAILED",
                "provider_ref": "provider-failed-001",
            }
        ),
        content_type="application/json",
        HTTP_X_WEBHOOK_TOKEN=settings.PAYMENTS_WEBHOOK_TOKEN,
    )
    assert failed_response.status_code == 201

    payment.refresh_from_db()
    assert payment.status == "FAILED"

    ar_response = client.get("/api/v1/finance/ar-receivables/")
    assert ar_response.status_code == 200
    ar_items = _extract_results(ar_response.json())
    ar_item = next(
        (
            item
            for item in ar_items
            if item["reference_type"] == "ORDER" and item["reference_id"] == order.id
        ),
        None,
    )

    assert ar_item is not None
    assert ar_item["status"] == "OPEN"

    movements = CashMovement.objects.filter(
        direction=CashDirection.IN,
        reference_type="AR",
        reference_id=ar_item["id"],
    )
    assert movements.count() == 0


@pytest.mark.django_db
def test_orders_create_com_payment_method_card_permite_intent_card(
    create_user_with_roles,
):
    delivery_date = date(2026, 4, 2)
    menu_item = _create_menu_item_for_api(delivery_date)

    customer = create_user_with_roles(
        username="cliente_checkout_card",
        role_codes=[SystemRole.CLIENTE],
    )
    customer_client = _auth_client(customer)

    create_response = customer_client.post(
        "/api/v1/orders/orders/",
        data=json.dumps(
            {
                "delivery_date": delivery_date.isoformat(),
                "payment_method": "CARD",
                "items": [{"menu_item": menu_item.id, "qty": 1}],
            }
        ),
        content_type="application/json",
    )
    assert create_response.status_code == 201

    order_body = create_response.json()
    assert order_body["payments"][0]["method"] == "CARD"

    payment_id = order_body["payments"][0]["id"]
    intent_response = customer_client.post(
        f"/api/v1/orders/payments/{payment_id}/intent/",
        data=json.dumps({}),
        content_type="application/json",
        HTTP_IDEMPOTENCY_KEY="intent-card-api-001",
    )

    assert intent_response.status_code == 201
    intent_body = intent_response.json()
    assert intent_body["client_payload"]["method"] == "CARD"
    assert "card" in intent_body["client_payload"]

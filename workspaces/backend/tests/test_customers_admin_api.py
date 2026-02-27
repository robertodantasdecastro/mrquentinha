import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.accounts.models import (
    CustomerLgpdRequest,
    UserProfile,
)
from apps.accounts.services import (
    SystemRole,
    assign_roles_to_user,
    ensure_default_roles,
)


@pytest.mark.django_db
def test_customers_admin_lista_clientes(client, create_user_with_roles):
    ensure_default_roles()
    customer = create_user_with_roles(
        username="cliente_area_admin",
        role_codes=[SystemRole.CLIENTE],
    )
    UserProfile.objects.create(
        user=customer,
        full_name="Cliente Teste",
        cpf="12345678901",
        city="Sao Paulo",
        state="SP",
    )

    create_user_with_roles(
        username="cozinha_sem_cliente",
        role_codes=[SystemRole.COZINHA],
    )

    response = client.get("/api/v1/accounts/customers/")

    assert response.status_code == 200
    payload = response.json()
    assert any(item["username"] == "cliente_area_admin" for item in payload)
    assert all("CLIENTE" in item["roles"] for item in payload)


@pytest.mark.django_db
def test_customers_admin_atualiza_status_e_bloqueia_checkout(
    client, create_user_with_roles
):
    customer = create_user_with_roles(
        username="cliente_bloqueio",
        role_codes=[SystemRole.CLIENTE],
    )

    response = client.post(
        f"/api/v1/accounts/customers/{customer.id}/status/",
        {
            "account_status": "SUSPENDED",
            "reason": "Chargeback recorrente.",
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["account_status"] == "SUSPENDED"
    assert payload["checkout_blocked"] is True

    customer.refresh_from_db()
    assert customer.is_active is False


@pytest.mark.django_db
def test_customers_admin_atualiza_consents(client, create_user_with_roles):
    customer = create_user_with_roles(
        username="cliente_consent",
        role_codes=[SystemRole.CLIENTE],
    )

    response = client.post(
        f"/api/v1/accounts/customers/{customer.id}/consents/",
        {
            "accepted_terms": True,
            "accepted_privacy_policy": True,
            "marketing_opt_in": False,
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["terms_accepted_at"] is not None
    assert payload["privacy_policy_accepted_at"] is not None
    assert payload["marketing_opt_out_at"] is not None


@pytest.mark.django_db
def test_customers_admin_cria_e_finaliza_solicitacao_lgpd(
    client, create_user_with_roles
):
    customer = create_user_with_roles(
        username="cliente_lgpd",
        role_codes=[SystemRole.CLIENTE],
    )

    create_response = client.post(
        f"/api/v1/accounts/customers/{customer.id}/lgpd-requests/",
        {
            "request_type": "ACCESS",
            "channel": "EMAIL",
            "requested_by_name": "Cliente LGPD",
            "requested_by_email": "cliente_lgpd@example.com",
            "notes": "Solicitacao de acesso aos dados cadastrais.",
        },
        format="json",
    )

    assert create_response.status_code == 201
    created_payload = create_response.json()
    assert created_payload["status"] == "OPEN"
    assert created_payload["protocol_code"].startswith("LGPD-")

    request_id = created_payload["id"]
    status_response = client.patch(
        f"/api/v1/accounts/customers/lgpd-requests/{request_id}/status/",
        {
            "status": "COMPLETED",
            "resolution_notes": "Arquivo entregue por e-mail para o titular.",
        },
        format="json",
    )

    assert status_response.status_code == 200
    status_payload = status_response.json()
    assert status_payload["status"] == "COMPLETED"
    assert status_payload["resolved_at"] is not None


@pytest.mark.django_db
def test_customers_admin_overview(client, create_user_with_roles):
    create_user_with_roles(
        username="cliente_overview_1",
        role_codes=[SystemRole.CLIENTE],
    )
    create_user_with_roles(
        username="cliente_overview_2",
        role_codes=[SystemRole.CLIENTE],
    )

    response = client.get("/api/v1/accounts/customers/overview/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 2
    assert "by_account_status" in payload


@pytest.mark.django_db
def test_customers_admin_requer_papel_de_gestao(anonymous_client):
    User = get_user_model()
    user = User.objects.create_user(
        username="cliente_sem_acesso_admin_clientes",
        password="senha_forte_123",
        email="cliente_sem_acesso_admin_clientes@example.com",
    )
    ensure_default_roles()
    assign_roles_to_user(
        user=user,
        role_codes=[SystemRole.CLIENTE],
        replace=True,
    )

    anonymous_client.force_authenticate(user=user)
    response = anonymous_client.get("/api/v1/accounts/customers/")

    assert response.status_code == 403


@pytest.mark.django_db
def test_customers_admin_resend_email_verification(client, create_user_with_roles):
    customer = create_user_with_roles(
        username="cliente_resend_email_admin",
        role_codes=[SystemRole.CLIENTE],
    )

    response = client.post(
        f"/api/v1/accounts/customers/{customer.id}/resend-email-verification/",
        {
            "preferred_client_base_url": "https://cliente-dev.trycloudflare.com",
        },
        format="json",
    )

    assert response.status_code in {200, 202}
    payload = response.json()
    assert "client_base_url" in payload
    profile = UserProfile.objects.get(user=customer)
    assert profile.email_verification_token_hash
    assert profile.email_verification_token_created_at is not None
    assert profile.email_verification_last_client_base_url


@pytest.mark.django_db
def test_customers_admin_lista_lgpd_requests_por_cliente(
    client, create_user_with_roles
):
    customer = create_user_with_roles(
        username="cliente_lgpd_lista",
        role_codes=[SystemRole.CLIENTE],
    )

    CustomerLgpdRequest.objects.create(
        customer=customer,
        protocol_code="LGPD-TESTE-0001",
        request_type=CustomerLgpdRequest.RequestType.ACCESS,
        status=CustomerLgpdRequest.RequestStatus.OPEN,
        channel=CustomerLgpdRequest.RequestChannel.WEB,
        requested_at=timezone.now(),
    )

    response = client.get(
        f"/api/v1/accounts/customers/{customer.id}/lgpd-requests/",
    )

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) >= 1

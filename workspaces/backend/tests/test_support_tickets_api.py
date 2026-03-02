import pytest
from django.utils import timezone
from rest_framework.test import APIClient

from apps.accounts.models import CustomerSupportMessage, CustomerSupportTicket
from apps.accounts.services import SystemRole, ensure_default_roles


@pytest.mark.django_db
def test_support_tickets_customer_flow(create_user_with_roles):
    ensure_default_roles()
    customer = create_user_with_roles(
        username="cliente_support",
        role_codes=[SystemRole.CLIENTE],
    )
    api_client = APIClient()
    api_client.force_authenticate(user=customer)

    response = api_client.post(
        "/api/v1/accounts/me/support-tickets/create/",
        {
            "subject": "Preciso de ajuda com meu pedido",
            "message": "Nao consigo acompanhar o status.",
            "channel": "WEB",
            "priority": "NORMAL",
        },
        format="json",
    )

    assert response.status_code == 201
    payload = response.json()
    ticket_id = payload["id"]
    assert payload["subject"] == "Preciso de ajuda com meu pedido"
    assert payload["status"] == "OPEN"
    assert len(payload["messages"]) == 1

    list_response = api_client.get("/api/v1/accounts/me/support-tickets/")
    assert list_response.status_code == 200
    assert any(item["id"] == ticket_id for item in list_response.json())

    message_response = api_client.post(
        f"/api/v1/accounts/me/support-tickets/{ticket_id}/messages/",
        {"message": "Ainda aguardando retorno."},
        format="json",
    )
    assert message_response.status_code == 201

    ticket = CustomerSupportTicket.objects.get(id=ticket_id)
    CustomerSupportMessage.objects.create(
        ticket=ticket,
        author=None,
        author_type=CustomerSupportMessage.AuthorType.AGENT,
        message="Nota interna",
        is_internal=True,
    )
    messages_response = api_client.get(
        f"/api/v1/accounts/me/support-tickets/{ticket_id}/messages/"
    )
    assert messages_response.status_code == 200
    assert all(not item["is_internal"] for item in messages_response.json())


@pytest.mark.django_db
def test_support_tickets_admin_flow(client, create_user_with_roles):
    ensure_default_roles()
    customer = create_user_with_roles(
        username="cliente_support_admin",
        role_codes=[SystemRole.CLIENTE],
    )
    ticket = CustomerSupportTicket.objects.create(
        customer=customer,
        subject="Erro no pagamento",
        channel=CustomerSupportTicket.Channel.WEB,
        priority=CustomerSupportTicket.Priority.HIGH,
        created_by=customer,
        last_activity_at=timezone.now(),
    )
    CustomerSupportMessage.objects.create(
        ticket=ticket,
        author=customer,
        author_type=CustomerSupportMessage.AuthorType.CUSTOMER,
        message="Nao consigo finalizar a compra.",
    )

    list_response = client.get("/api/v1/accounts/support-tickets/")
    assert list_response.status_code == 200
    assert any(item["id"] == ticket.id for item in list_response.json())

    update_response = client.patch(
        f"/api/v1/accounts/support-tickets/{ticket.id}/",
        {
            "status": "RESOLVED",
            "priority": "URGENT",
            "internal_note": "Confirmado ajuste no gateway.",
        },
        format="json",
    )
    assert update_response.status_code == 200
    updated_payload = update_response.json()
    assert updated_payload["status"] == "RESOLVED"
    assert updated_payload["closed_at"] is not None

    messages_response = client.get(
        f"/api/v1/accounts/support-tickets/{ticket.id}/messages/"
    )
    assert messages_response.status_code == 200
    assert any(item["is_internal"] for item in messages_response.json())

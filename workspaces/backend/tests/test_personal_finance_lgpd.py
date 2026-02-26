from datetime import timedelta

import pytest
from django.core.management import call_command
from django.utils import timezone

from apps.personal_finance.models import PersonalAuditEvent, PersonalAuditLog
from apps.personal_finance.services import record_personal_audit_log


@pytest.mark.django_db
def test_personal_finance_export_requer_autenticacao(anonymous_client):
    response = anonymous_client.get("/api/v1/personal-finance/export/")

    assert response.status_code == 401


@pytest.mark.django_db
def test_personal_finance_export_retorna_apenas_dados_do_owner(
    client,
    anonymous_client,
    create_user_with_roles,
):
    account_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta principal",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert account_response.status_code == 201

    secondary_user = create_user_with_roles(username="owner_secundario")
    anonymous_client.force_authenticate(user=secondary_user)
    secondary_response = anonymous_client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta secundaria",
            "type": "CASH",
            "is_active": True,
        },
        format="json",
    )
    assert secondary_response.status_code == 201

    export_response = client.get("/api/v1/personal-finance/export/")

    assert export_response.status_code == 200
    payload = export_response.json()

    assert payload["owner"]["username"] == "admin_test"
    accounts = payload["data"]["accounts"]
    assert len(accounts) == 1
    assert accounts[0]["name"] == "Conta principal"


@pytest.mark.django_db
def test_personal_finance_audit_logs_registram_eventos_basicos(client):
    create_response = client.post(
        "/api/v1/personal-finance/accounts/",
        {
            "name": "Conta log",
            "type": "CHECKING",
            "is_active": True,
        },
        format="json",
    )
    assert create_response.status_code == 201

    list_response = client.get("/api/v1/personal-finance/accounts/")
    assert list_response.status_code == 200

    audit_response = client.get("/api/v1/personal-finance/audit-logs/")
    assert audit_response.status_code == 200

    events = {
        (item["event_type"], item["resource_type"]) for item in audit_response.json()
    }
    assert (PersonalAuditEvent.CREATE, "ACCOUNT") in events
    assert (PersonalAuditEvent.LIST, "ACCOUNT") in events


@pytest.mark.django_db
def test_purge_personal_audit_logs_remove_apenas_registros_antigos(
    create_user_with_roles,
):
    owner = create_user_with_roles(username="owner_retencao")

    old_log = record_personal_audit_log(
        owner=owner,
        event_type=PersonalAuditEvent.LIST,
        resource_type="ACCOUNT",
        metadata={"scenario": "old"},
    )
    recent_log = record_personal_audit_log(
        owner=owner,
        event_type=PersonalAuditEvent.CREATE,
        resource_type="ENTRY",
        metadata={"scenario": "recent"},
    )

    PersonalAuditLog.objects.filter(pk=old_log.pk).update(
        created_at=timezone.now() - timedelta(days=800)
    )

    call_command("purge_personal_audit_logs", days=730)

    assert not PersonalAuditLog.objects.filter(pk=old_log.pk).exists()
    assert PersonalAuditLog.objects.filter(pk=recent_log.pk).exists()

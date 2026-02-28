import pytest

from apps.admin_audit.models import AdminActivityLog


@pytest.mark.django_db
def test_admin_activity_log_registra_requisicao_de_usuario_admin(client):
    response = client.get(
        "/api/v1/portal/admin/config/",
        HTTP_ORIGIN="http://10.211.55.21:3002",
    )

    assert response.status_code == 200
    entry = AdminActivityLog.objects.order_by("-id").first()
    assert entry is not None
    assert entry.actor_username == "admin_test"
    assert entry.channel in {"web-admin", "admin-authenticated"}
    assert entry.path == "/api/v1/portal/admin/config/"
    assert entry.method == "GET"


@pytest.mark.django_db
def test_admin_activity_log_sanitiza_payload_sensivel_em_login_admin(
    anonymous_client,
    admin_user,
):
    response = anonymous_client.post(
        "/api/v1/accounts/token/",
        data={
            "username": admin_user.username,
            "password": "admin_test_123",
        },
        format="json",
        HTTP_ORIGIN="http://10.211.55.21:3002",
    )

    assert response.status_code == 200
    entry = AdminActivityLog.objects.order_by("-id").first()
    assert entry is not None
    assert entry.actor is None
    assert entry.path == "/api/v1/accounts/token/"
    payload = entry.metadata.get("request_payload", {})
    assert payload.get("username") == admin_user.username
    assert payload.get("password") == "***"


@pytest.mark.django_db
def test_admin_activity_endpoint_lista_logs(client, admin_user):
    AdminActivityLog.objects.create(
        actor=admin_user,
        actor_username="admin_test",
        actor_is_staff=False,
        actor_is_superuser=False,
        channel="web-admin",
        method="GET",
        path="/api/v1/orders/",
        action_group="orders",
        resource="",
        http_status=200,
        is_success=True,
        duration_ms=42,
    )
    AdminActivityLog.objects.create(
        actor=admin_user,
        actor_username="admin_test",
        actor_is_staff=False,
        actor_is_superuser=False,
        channel="web-admin",
        method="POST",
        path="/api/v1/orders/",
        action_group="orders",
        resource="",
        http_status=201,
        is_success=True,
        duration_ms=91,
    )

    response = client.get("/api/v1/admin-audit/admin-activity/?limit=1&offset=0")

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 2
    assert payload["limit"] == 1
    assert len(payload["results"]) == 1
    assert payload["next_offset"] == 1


@pytest.mark.django_db
def test_admin_activity_endpoint_nao_gera_log_de_auto_consulta(client, admin_user):
    AdminActivityLog.objects.create(
        actor=admin_user,
        actor_username="admin_test",
        actor_is_staff=False,
        actor_is_superuser=False,
        channel="web-admin",
        method="GET",
        path="/api/v1/orders/",
        action_group="orders",
        resource="",
        http_status=200,
        is_success=True,
        duration_ms=24,
    )
    before_count = AdminActivityLog.objects.count()

    response = client.get("/api/v1/admin-audit/admin-activity/?limit=20&offset=0")

    assert response.status_code == 200
    assert AdminActivityLog.objects.count() == before_count

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import override_settings
from rest_framework.test import APIClient

from apps.portal.services import ensure_portal_config


@pytest.mark.django_db
def test_portal_public_config_get_sem_auth_retorna_200(anonymous_client):
    ensure_portal_config()

    response = anonymous_client.get("/api/v1/portal/config/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["active_template"]
    assert payload["client_active_template"]
    assert payload["admin_active_template"]
    assert payload["local_hostname"] == "mrquentinha"
    assert payload["backend_base_url"].endswith(":8000")
    assert payload["app_download_android_url"].endswith("/app/downloads/android.apk")
    assert payload["app_download_ios_url"].endswith("/app/downloads/ios")
    assert "auth_providers" in payload
    assert payload["auth_providers"]["google"]["enabled"] is False
    assert "client_secret" not in payload["auth_providers"]["google"]
    assert "payment_providers" in payload
    assert payload["payment_providers"]["default_provider"] == "mock"
    assert "cloudflare" in payload
    assert payload["cloudflare"]["enabled"] is False
    assert "sections" in payload


@pytest.mark.django_db
def test_portal_public_config_client_channel_retorna_200(anonymous_client):
    ensure_portal_config()

    response = anonymous_client.get("/api/v1/portal/config/?channel=client&page=home")

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "client"
    assert payload["active_template"] == payload["client_active_template"]
    assert isinstance(payload["client_available_templates"], list)


@pytest.mark.django_db
def test_portal_public_config_admin_channel_retorna_200(anonymous_client):
    ensure_portal_config()

    response = anonymous_client.get("/api/v1/portal/config/?channel=admin&page=home")

    assert response.status_code == 200
    payload = response.json()
    assert payload["channel"] == "admin"
    assert payload["active_template"] == payload["admin_active_template"]
    assert isinstance(payload["admin_available_templates"], list)


@pytest.mark.django_db
def test_portal_admin_endpoints_bloqueados_para_nao_admin(anonymous_client):
    no_auth_response = anonymous_client.get("/api/v1/portal/admin/sections/")
    assert no_auth_response.status_code in {401, 403}

    User = get_user_model()
    regular_user = User.objects.create_user(
        username="portal_regular",
        password="portal_regular_123",
    )
    regular_client = APIClient()
    regular_client.force_authenticate(user=regular_user)

    forbidden_response = regular_client.get("/api/v1/portal/admin/sections/")
    assert forbidden_response.status_code == 403


@pytest.mark.django_db
def test_portal_admin_cria_e_edita_section(client):
    config = ensure_portal_config()

    create_response = client.post(
        "/api/v1/portal/admin/sections/",
        data={
            "config": config.id,
            "template_id": "classic",
            "page": "home",
            "key": "cta-banner",
            "title": "CTA",
            "body_json": {"label": "Peca agora"},
            "is_enabled": True,
            "sort_order": 99,
        },
        format="json",
    )
    assert create_response.status_code == 201

    section_id = create_response.json()["id"]
    update_response = client.patch(
        f"/api/v1/portal/admin/sections/{section_id}/",
        data={"title": "CTA Atualizado"},
        format="json",
    )
    assert update_response.status_code == 200
    assert update_response.json()["title"] == "CTA Atualizado"


@pytest.mark.django_db
def test_mobile_release_latest_publico_retorna_payload_base(anonymous_client):
    ensure_portal_config()

    response = anonymous_client.get("/api/v1/portal/mobile/releases/latest/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["api_base_url"].endswith(":8000")
    assert payload["android_download_url"].endswith("/app/downloads/android.apk")
    assert payload["ios_download_url"].endswith("/app/downloads/ios")


@pytest.mark.django_db
def test_mobile_release_admin_cria_compila_e_publica(client):
    config = ensure_portal_config()
    create_response = client.post(
        "/api/v1/portal/admin/mobile/releases/",
        data={
            "config": config.id,
            "release_version": "1.0.0",
            "build_number": 1,
            "update_policy": "OPTIONAL",
            "is_critical_update": False,
            "min_supported_version": "1.0.0",
            "recommended_version": "1.0.0",
            "release_notes": "Release inicial",
        },
        format="json",
    )
    assert create_response.status_code == 201
    created_payload = create_response.json()
    assert created_payload["status"] == "SIGNED"

    release_id = created_payload["id"]
    publish_response = client.post(
        f"/api/v1/portal/admin/mobile/releases/{release_id}/publish/",
        data={},
        format="json",
    )
    assert publish_response.status_code == 200
    assert publish_response.json()["status"] == "PUBLISHED"


@pytest.mark.django_db
def test_portal_admin_atualiza_auth_providers_google_apple(client):
    config = ensure_portal_config()

    response = client.patch(
        f"/api/v1/portal/admin/config/{config.id}/",
        data={
            "auth_providers": {
                "google": {
                    "enabled": True,
                    "web_client_id": "google-web-client-id",
                    "client_secret": "google-client-secret",
                },
                "apple": {
                    "enabled": True,
                    "service_id": "com.mrquentinha.web",
                    "team_id": "TEAM123",
                    "key_id": "KEY123",
                    "private_key": "PRIVATE_KEY",
                },
            }
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["auth_providers"]["google"]["enabled"] is True
    assert payload["auth_providers"]["apple"]["enabled"] is True

    public_response = client.get("/api/v1/portal/config/?channel=client&page=home")
    assert public_response.status_code == 200
    public_payload = public_response.json()
    assert public_payload["auth_providers"]["google"]["configured"] is True
    assert public_payload["auth_providers"]["apple"]["configured"] is True
    assert "client_secret" not in public_payload["auth_providers"]["google"]
    assert "private_key" not in public_payload["auth_providers"]["apple"]


@pytest.mark.django_db
def test_portal_admin_atualiza_payment_providers(client):
    config = ensure_portal_config()

    response = client.patch(
        f"/api/v1/portal/admin/config/{config.id}/",
        data={
            "payment_providers": {
                "default_provider": "asaas",
                "enabled_providers": ["asaas", "mercadopago"],
                "frontend_provider": {
                    "web": "mercadopago",
                    "mobile": "asaas",
                },
                "method_provider_order": {
                    "PIX": ["asaas", "mercadopago"],
                    "CARD": ["mercadopago"],
                    "VR": ["mock"],
                },
                "receiver": {
                    "person_type": "CNPJ",
                    "document": "12345678000195",
                    "name": "Mr Quentinha LTDA",
                    "email": "financeiro@mrquentinha.com.br",
                },
                "asaas": {
                    "enabled": True,
                    "api_key": "asaas-secret",
                },
                "mercadopago": {
                    "enabled": True,
                    "access_token": "mp-secret",
                },
            }
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["payment_providers"]["default_provider"] == "asaas"
    assert "asaas" in payload["payment_providers"]["enabled_providers"]
    assert payload["payment_providers"]["frontend_provider"]["web"] == "mercadopago"
    assert payload["payment_providers"]["frontend_provider"]["mobile"] == "asaas"

    public_response = client.get("/api/v1/portal/config/?channel=client&page=home")
    assert public_response.status_code == 200
    public_payload = public_response.json()
    assert public_payload["payment_providers"]["asaas"]["configured"] is True
    assert public_payload["payment_providers"]["mercadopago"]["configured"] is True
    assert "api_key" not in public_payload["payment_providers"]["asaas"]
    assert "access_token" not in public_payload["payment_providers"]["mercadopago"]


@pytest.mark.django_db
def test_portal_admin_atualiza_email_settings(client):
    config = ensure_portal_config()

    response = client.patch(
        f"/api/v1/portal/admin/config/{config.id}/",
        data={
            "email_settings": {
                "enabled": False,
                "backend": "django.core.mail.backends.smtp.EmailBackend",
                "host": "smtp.example.com",
                "port": 587,
                "username": "smtp_user",
                "password": "smtp_password",
                "use_tls": True,
                "use_ssl": False,
                "timeout_seconds": 20,
                "from_name": "Mr Quentinha",
                "from_email": "noreply@mrquentinha.com.br",
                "reply_to_email": "suporte@mrquentinha.com.br",
                "test_recipient": "teste@mrquentinha.com.br",
            }
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["email_settings"]["host"] == "smtp.example.com"
    assert payload["email_settings"]["port"] == 587
    assert payload["email_settings"]["from_email"] == "noreply@mrquentinha.com.br"


@pytest.mark.django_db
@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
def test_portal_admin_test_email_action(client):
    response = client.post(
        "/api/v1/portal/admin/config/test-email/",
        data={"to_email": "qa@mrquentinha.com.br"},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["to_email"] == "qa@mrquentinha.com.br"
    assert len(mail.outbox) == 1


@pytest.mark.django_db
def test_portal_admin_test_payment_provider_action(client, monkeypatch):
    captured_provider: dict[str, str] = {}

    def fake_test_payment_provider_connection(provider_name: str):
        captured_provider["name"] = provider_name
        return {"provider": provider_name, "ok": True, "detail": "ok"}

    monkeypatch.setattr(
        "apps.portal.views.test_payment_provider_connection",
        fake_test_payment_provider_connection,
    )

    response = client.post(
        "/api/v1/portal/admin/config/test-payment-provider/",
        data={"provider": "asaas"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_database_ssh_probe_action(client, monkeypatch):
    def fake_probe(*, payload=None):
        return {
            "ok": True,
            "check": {"status": "ok", "detail": "Conectividade SSH validada."},
            "ssh": {"host": "44.192.27.104"},
        }

    monkeypatch.setattr(
        "apps.portal.views.validate_database_ssh_connectivity",
        fake_probe,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/ssh/probe/",
        data={"ssh": {"host": "44.192.27.104", "user": "ubuntu"}},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["check"]["status"] == "ok"


@pytest.mark.django_db
def test_portal_admin_database_backups_list_action(client, monkeypatch):
    def fake_list(*, limit=30):
        assert limit == 15
        return {
            "ok": True,
            "count": 1,
            "results": [
                {
                    "path": "/tmp/test.dump",
                    "filename": "test.dump",
                    "size_bytes": 123,
                    "updated_at": "2026-03-03T00:00:00",
                }
            ],
        }

    monkeypatch.setattr(
        "apps.portal.views.list_remote_database_backups",
        fake_list,
    )

    response = client.get("/api/v1/portal/admin/config/database/backups/?limit=15")

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["count"] == 1


@pytest.mark.django_db
def test_portal_admin_database_backup_create_action(client, monkeypatch):
    def fake_create(*, payload=None):
        assert isinstance(payload, dict)
        return {
            "ok": True,
            "label": "manual",
            "backup_file": "/tmp/backup.dump",
            "metadata_file": "/tmp/backup.json",
            "size_bytes": 456,
            "ssh_target": "ubuntu@44.192.27.104",
        }

    monkeypatch.setattr(
        "apps.portal.views.create_remote_database_backup",
        fake_create,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/backups/create/",
        data={"label": "manual"},
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["ok"] is True
    assert payload["backup_file"].endswith(".dump")


@pytest.mark.django_db
def test_portal_admin_database_tunnel_action(client, monkeypatch):
    def fake_manage(*, action):
        assert action == "status"
        return {
            "ok": True,
            "action": "status",
            "tunnel": {
                "status": "inactive",
                "pid": None,
            },
        }

    monkeypatch.setattr(
        "apps.portal.views.manage_database_ssh_tunnel",
        fake_manage,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/tunnel/action/",
        data={"action": "status"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_database_psql_execute_action(client, monkeypatch):
    def fake_run(*, payload=None):
        assert payload["read_only"] is True
        return {
            "ok": True,
            "exit_code": 0,
            "stdout": "ok",
            "stderr": "",
            "command_preview": "ssh ...",
        }

    monkeypatch.setattr(
        "apps.portal.views.run_remote_psql_command",
        fake_run,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/psql/execute/",
        data={"command": "SELECT 1;", "read_only": True},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_database_django_sync_action(client, monkeypatch):
    def fake_sync(*, payload=None):
        assert payload["mode"] == "dump"
        return {
            "ok": True,
            "mode": "dump",
            "local_dump_file": "/tmp/django_dump.json",
            "synced": False,
            "exclude_apps": ["contenttypes"],
        }

    monkeypatch.setattr(
        "apps.portal.views.sync_remote_database_via_django",
        fake_sync,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/django/sync/",
        data={"mode": "dump", "exclude_apps": ["contenttypes"]},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_database_django_dbbackup_action(client, monkeypatch):
    def fake_dbbackup(*, payload=None):
        assert payload["mode"] == "list"
        return {
            "ok": True,
            "mode": "list",
            "exit_code": 0,
            "stdout": "backup_001",
            "stderr": "",
            "command_preview": "ssh ... listbackups",
        }

    monkeypatch.setattr(
        "apps.portal.views.run_remote_django_dbbackup",
        fake_dbbackup,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/django-dbbackup/",
        data={"mode": "list"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_database_copy_scp_action(client, monkeypatch):
    def fake_copy(*, payload=None):
        assert payload["backup_file"] == "/tmp/remote.dump"
        return {
            "ok": True,
            "source_backup_file": payload["backup_file"],
            "local_dump_file": "/tmp/local.dump",
            "local_dump_size_bytes": 123,
            "transfer_method": "scp",
        }

    monkeypatch.setattr(
        "apps.portal.views.copy_remote_backup_to_dev_via_scp",
        fake_copy,
    )

    response = client.post(
        "/api/v1/portal/admin/config/database/backups/fetch-dev/",
        data={"backup_file": "/tmp/remote.dump"},
        format="json",
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_database_command_catalog_action(client, monkeypatch):
    def fake_catalog(*, sample_backup_file=""):
        assert sample_backup_file == "/tmp/backup.dump"
        return {
            "ok": True,
            "commands": {"tunnel_start": "ssh -N -L ..."},
            "notes": ["ok"],
        }

    monkeypatch.setattr(
        "apps.portal.views.build_database_ops_command_catalog",
        fake_catalog,
    )

    response = client.get(
        "/api/v1/portal/admin/config/database/commands/catalog/?sample_backup_file=/tmp/backup.dump"
    )
    assert response.status_code == 200
    assert response.json()["ok"] is True


@pytest.mark.django_db
def test_portal_admin_cloudflare_preview_e_toggle(client):
    preview_response = client.post(
        "/api/v1/portal/admin/config/cloudflare-preview/",
        data={
            "settings": {
                "mode": "hybrid",
                "root_domain": "mrquentinha.com.br",
                "subdomains": {
                    "portal": "www",
                    "client": "app",
                    "admin": "admin",
                    "api": "api",
                },
                "tunnel_name": "mrquentinha",
            }
        },
        format="json",
    )
    assert preview_response.status_code == 200
    preview_payload = preview_response.json()
    assert preview_payload["urls"]["api_base_url"] == "https://api.mrquentinha.com.br"

    toggle_on_response = client.post(
        "/api/v1/portal/admin/config/cloudflare-toggle/",
        data={
            "enabled": True,
            "settings": {
                "mode": "hybrid",
                "root_domain": "mrquentinha.com.br",
                "subdomains": {
                    "portal": "www",
                    "client": "app",
                    "admin": "admin",
                    "api": "api",
                },
                "tunnel_name": "mrquentinha",
            },
        },
        format="json",
    )
    assert toggle_on_response.status_code == 200
    toggle_on_payload = toggle_on_response.json()
    assert toggle_on_payload["enabled"] is True
    assert (
        toggle_on_payload["config"]["api_base_url"] == "https://api.mrquentinha.com.br"
    )
    assert toggle_on_payload["config"]["cloudflare_settings"]["enabled"] is True

    toggle_off_response = client.post(
        "/api/v1/portal/admin/config/cloudflare-toggle/",
        data={"enabled": False},
        format="json",
    )
    assert toggle_off_response.status_code == 200
    toggle_off_payload = toggle_off_response.json()
    assert toggle_off_payload["enabled"] is False
    assert toggle_off_payload["config"]["cloudflare_settings"]["enabled"] is False


@pytest.mark.django_db
def test_portal_admin_cloudflare_runtime_action(client, monkeypatch):
    def fake_manage_cloudflare_runtime(*, action: str):
        config = ensure_portal_config()
        return config, {
            "state": "active" if action in {"start", "refresh"} else "inactive",
            "pid": 12345 if action in {"start", "refresh"} else None,
            "log_file": "/tmp/cloudflare.log",
            "last_started_at": "",
            "last_stopped_at": "",
            "last_error": "",
            "run_command": "cloudflared tunnel run mrquentinha",
            "last_log_lines": [],
        }

    monkeypatch.setattr(
        "apps.portal.views.manage_cloudflare_runtime",
        fake_manage_cloudflare_runtime,
    )

    response = client.post(
        "/api/v1/portal/admin/config/cloudflare-runtime/",
        data={"action": "status"},
        format="json",
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["action"] == "status"
    assert "runtime" in payload

    refresh_response = client.post(
        "/api/v1/portal/admin/config/cloudflare-runtime/",
        data={"action": "refresh"},
        format="json",
    )
    assert refresh_response.status_code == 200
    refresh_payload = refresh_response.json()
    assert refresh_payload["action"] == "refresh"
    assert refresh_payload["runtime"]["state"] == "active"


@pytest.mark.django_db
def test_portal_admin_installer_wizard_endpoints(client, monkeypatch):
    config = ensure_portal_config()

    monkeypatch.setattr(
        "apps.portal.views.validate_installer_wizard_payload",
        lambda *, payload: {
            "ok": True,
            "normalized_payload": payload,
            "warnings": [],
            "workflow_version": "2026.02.28",
            "validated_at": "2026-02-28T00:00:00Z",
        },
    )
    monkeypatch.setattr(
        "apps.portal.views.save_installer_wizard_settings",
        lambda *, payload, completed_step: config,
    )
    monkeypatch.setattr(
        "apps.portal.views.validate_installer_aws_setup",
        lambda *, payload: {
            "ok": True,
            "workflow_version": "2026.02.28",
            "validated_at": "2026-03-01T00:00:00Z",
            "normalized_payload": payload,
            "warnings": [],
            "cloud_validation": {
                "provider": "aws",
                "checked_at": "2026-03-01T00:00:00Z",
                "connectivity": {
                    "name": "aws_connectivity",
                    "status": "ok",
                    "detail": "ok",
                },
                "prerequisites": {"checks": [], "warnings": []},
                "costs": {
                    "currency": "USD",
                    "estimated_monthly_total_usd": 50.0,
                    "estimated_monthly_range_usd": {"min": 40.0, "max": 60.0},
                    "breakdown": [],
                    "current_month_cost": {
                        "available": False,
                        "detail": "indisponivel",
                        "month_start": "",
                        "month_end_exclusive": "",
                        "total_mtd_usd": 0.0,
                        "top_services": [],
                    },
                    "notes": [],
                },
                "warnings": [],
            },
        },
    )
    monkeypatch.setattr(
        "apps.portal.views.start_installer_job",
        lambda *, payload, initiated_by: (
            config,
            {
                "job_id": "job-1",
                "status": "running",
                "target": "local",
                "mode": "dev",
                "stack": "vm",
            },
        ),
    )
    monkeypatch.setattr(
        "apps.portal.views.get_installer_job_status",
        lambda *, job_id: (
            config,
            {
                "job_id": job_id,
                "status": "running",
                "last_log_lines": ["ok"],
            },
        ),
    )
    monkeypatch.setattr(
        "apps.portal.views.cancel_installer_job",
        lambda *, job_id: (
            config,
            {
                "job_id": job_id,
                "status": "canceled",
            },
        ),
    )
    monkeypatch.setattr(
        "apps.portal.views.list_installer_jobs",
        lambda *, limit=20: [{"job_id": "job-1", "status": "running"}],
    )

    validate_response = client.post(
        "/api/v1/portal/admin/config/installer-wizard-validate/",
        data={"payload": {"mode": "dev", "stack": "vm", "target": "local"}},
        format="json",
    )
    assert validate_response.status_code == 200
    assert validate_response.json()["ok"] is True

    aws_validate_response = client.post(
        "/api/v1/portal/admin/config/installer-cloud/aws/validate/",
        data={
            "payload": {
                "mode": "dev",
                "stack": "vm",
                "target": "aws",
                "cloud": {"provider": "aws", "region": "sa-east-1"},
            }
        },
        format="json",
    )
    assert aws_validate_response.status_code == 200
    assert aws_validate_response.json()["cloud_validation"]["provider"] == "aws"

    save_response = client.post(
        "/api/v1/portal/admin/config/installer-wizard-save/",
        data={
            "payload": {"mode": "dev", "stack": "vm", "target": "local"},
            "completed_step": "review",
        },
        format="json",
    )
    assert save_response.status_code == 200
    assert "installer_settings" in save_response.json()

    start_response = client.post(
        "/api/v1/portal/admin/config/installer-jobs/start/",
        data={"payload": {"mode": "dev", "stack": "vm", "target": "local"}},
        format="json",
    )
    assert start_response.status_code == 200
    assert start_response.json()["job"]["job_id"] == "job-1"

    status_response = client.get(
        "/api/v1/portal/admin/config/installer-jobs/job-1/status/"
    )
    assert status_response.status_code == 200
    assert status_response.json()["job"]["job_id"] == "job-1"

    cancel_response = client.post(
        "/api/v1/portal/admin/config/installer-jobs/job-1/cancel/",
        data={},
        format="json",
    )
    assert cancel_response.status_code == 200
    assert cancel_response.json()["job"]["status"] == "canceled"

    list_response = client.get("/api/v1/portal/admin/config/installer-jobs/")
    assert list_response.status_code == 200
    assert list_response.json()["results"][0]["job_id"] == "job-1"

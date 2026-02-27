import pytest
from django.contrib.auth import get_user_model
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
                    "document": "12345678000190",
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
            "state": "active" if action == "start" else "inactive",
            "pid": 12345 if action == "start" else None,
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

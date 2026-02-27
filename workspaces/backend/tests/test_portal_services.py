import pytest
from django.core.exceptions import ValidationError

from apps.portal.models import PortalConfig, PortalSection
from apps.portal.services import (
    build_cloudflare_preview,
    build_latest_mobile_release_payload,
    build_public_portal_payload,
    compile_mobile_release,
    create_mobile_release,
    ensure_portal_config,
    manage_cloudflare_runtime,
    publish_mobile_release,
    save_portal_config,
    toggle_cloudflare_mode,
)


@pytest.mark.django_db
def test_portal_config_singleton():
    first = ensure_portal_config()
    second = ensure_portal_config()

    assert first.id == second.id
    assert first.singleton_key == "default"
    assert first.local_hostname == "mrquentinha"
    assert first.portal_base_url == "https://10.211.55.21:3000"
    assert first.api_base_url == "https://10.211.55.21:8000"
    assert any(
        item["id"] == "client-vitrine-fit" for item in first.client_available_templates
    )
    assert any(
        item["id"] == "admin-adminkit" for item in first.admin_available_templates
    )
    assert any(
        item["id"] == "admin-admindek" for item in first.admin_available_templates
    )
    assert first.admin_active_template == "admin-classic"
    assert "google" in first.auth_providers
    assert "apple" in first.auth_providers
    assert first.payment_providers["default_provider"] == "mock"
    assert "mock" in first.payment_providers["enabled_providers"]
    assert first.payment_providers["frontend_provider"]["web"] == "mock"
    assert first.payment_providers["frontend_provider"]["mobile"] == "mock"


@pytest.mark.django_db
def test_ensure_portal_config_preenche_cors_padrao_quando_vazio():
    PortalConfig.objects.create(
        singleton_key=PortalConfig.SINGLETON_KEY,
        cors_allowed_origins=[],
    )

    config = ensure_portal_config()

    assert config.cors_allowed_origins == [
        "https://10.211.55.21:3000",
        "https://10.211.55.21:3001",
        "https://10.211.55.21:3002",
        "http://mrquentinha:3000",
        "http://mrquentinha:3001",
        "http://mrquentinha:3002",
        "http://10.211.55.21:3000",
        "http://10.211.55.21:3001",
        "http://10.211.55.21:3002",
    ]


@pytest.mark.django_db
def test_build_public_payload_filtra_por_template_page_e_enabled_ordenado():
    config, _ = save_portal_config(
        payload={
            "active_template": "template-teste",
            "available_templates": [
                {"id": "template-teste", "label": "Template Teste"},
                {"id": "letsfit-clean", "label": "LetsFit Clean"},
            ],
            "client_active_template": "client-classic",
            "client_available_templates": [
                {"id": "client-classic", "label": "Cliente Classico"},
                {"id": "client-quentinhas", "label": "Cliente Quentinhas"},
            ],
        }
    )

    PortalSection.objects.create(
        config=config,
        template_id="template-teste",
        page="home",
        key="hero",
        title="Hero",
        body_json={"text": "hero"},
        is_enabled=True,
        sort_order=20,
    )
    PortalSection.objects.create(
        config=config,
        template_id="template-teste",
        page="home",
        key="benefits",
        title="Benefits",
        body_json={"text": "benefits"},
        is_enabled=True,
        sort_order=10,
    )
    PortalSection.objects.create(
        config=config,
        template_id="template-teste",
        page="home",
        key="disabled",
        title="Disabled",
        body_json={"text": "disabled"},
        is_enabled=False,
        sort_order=5,
    )
    PortalSection.objects.create(
        config=config,
        template_id="letsfit-clean",
        page="home",
        key="other-template",
        title="Other",
        body_json={"text": "other"},
        is_enabled=True,
        sort_order=1,
    )
    PortalSection.objects.create(
        config=config,
        template_id="template-teste",
        page="contato",
        key="other-page",
        title="Other Page",
        body_json={"text": "other-page"},
        is_enabled=True,
        sort_order=2,
    )

    payload = build_public_portal_payload(page="home")

    assert payload["active_template"] == "template-teste"
    assert payload["channel"] == "portal"
    assert [section["key"] for section in payload["sections"]] == [
        "benefits",
        "hero",
    ]


@pytest.mark.django_db
def test_build_public_payload_client_retorna_template_do_web_cliente():
    config, _ = save_portal_config(
        payload={
            "active_template": "classic",
            "available_templates": [{"id": "classic", "label": "Classic"}],
            "client_active_template": "client-quentinhas",
            "client_available_templates": [
                {"id": "client-classic", "label": "Cliente Classico"},
                {"id": "client-quentinhas", "label": "Cliente Quentinhas"},
            ],
        }
    )

    PortalSection.objects.create(
        config=config,
        template_id="client-quentinhas",
        page="home",
        key="hero",
        title="Hero Cliente",
        body_json={"text": "cliente"},
        is_enabled=True,
        sort_order=10,
    )

    payload = build_public_portal_payload(page="home", channel="client")

    assert payload["channel"] == "client"
    assert payload["active_template"] == "client-quentinhas"
    assert payload["client_active_template"] == "client-quentinhas"
    assert payload["sections"][0]["key"] == "hero"


@pytest.mark.django_db
def test_build_public_payload_admin_retorna_template_do_web_admin():
    config, _ = save_portal_config(
        payload={
            "admin_active_template": "admin-adminkit",
            "admin_available_templates": [
                {"id": "admin-classic", "label": "Admin Classico"},
                {"id": "admin-adminkit", "label": "Admin Operations Kit"},
            ],
        }
    )

    payload = build_public_portal_payload(page="home", channel="admin")

    assert payload["channel"] == "admin"
    assert payload["active_template"] == "admin-adminkit"
    assert payload["admin_active_template"] == "admin-adminkit"
    assert any(
        item["id"] == "admin-adminkit" for item in payload["admin_available_templates"]
    )
    assert config.admin_active_template == "admin-adminkit"


@pytest.mark.django_db
def test_build_public_payload_auth_providers_nao_expoe_segredos():
    config, _ = save_portal_config(
        payload={
            "auth_providers": {
                "google": {
                    "enabled": True,
                    "web_client_id": "google-web-id",
                    "client_secret": "google-secret",
                },
                "apple": {
                    "enabled": True,
                    "service_id": "apple-service-id",
                    "private_key": "apple-private-key",
                    "team_id": "apple-team-id",
                    "key_id": "apple-key-id",
                },
            }
        }
    )

    payload = build_public_portal_payload(page="home", channel="client")
    auth_providers = payload["auth_providers"]

    assert auth_providers["google"]["enabled"] is True
    assert auth_providers["google"]["configured"] is True
    assert auth_providers["apple"]["enabled"] is True
    assert auth_providers["apple"]["configured"] is True

    assert "client_secret" not in auth_providers["google"]
    assert "private_key" not in auth_providers["apple"]
    assert config.auth_providers["google"]["client_secret"] == "google-secret"


@pytest.mark.django_db
def test_build_public_payload_payment_providers_nao_expoe_segredos():
    config, _ = save_portal_config(
        payload={
            "payment_providers": {
                "default_provider": "asaas",
                "enabled_providers": ["asaas", "mercadopago"],
                "frontend_provider": {
                    "web": "mercadopago",
                    "mobile": "asaas",
                },
                "method_provider_order": {
                    "PIX": ["asaas"],
                    "CARD": ["mercadopago"],
                    "VR": ["mock"],
                },
                "asaas": {
                    "enabled": True,
                    "api_base_url": "https://sandbox.asaas.com/api/v3",
                    "api_key": "asaas-secret",
                },
                "mercadopago": {
                    "enabled": True,
                    "api_base_url": "https://api.mercadopago.com",
                    "access_token": "mp-secret",
                },
            }
        }
    )

    payload = build_public_portal_payload(page="home", channel="client")
    payment_providers = payload["payment_providers"]

    assert payment_providers["default_provider"] == "asaas"
    assert payment_providers["frontend_provider"]["web"] == "mercadopago"
    assert payment_providers["frontend_provider"]["mobile"] == "asaas"
    assert payment_providers["asaas"]["configured"] is True
    assert payment_providers["mercadopago"]["configured"] is True
    assert "api_key" not in payment_providers["asaas"]
    assert "access_token" not in payment_providers["mercadopago"]
    assert config.payment_providers["asaas"]["api_key"] == "asaas-secret"


@pytest.mark.django_db
def test_build_latest_mobile_release_payload_retorna_release_publicada():
    release = create_mobile_release(
        payload={
            "release_version": "1.2.3",
            "build_number": 4,
            "update_policy": "FORCE",
            "is_critical_update": True,
            "min_supported_version": "1.2.0",
            "recommended_version": "1.2.3",
            "release_notes": "Atualizacao de seguranca.",
        }
    )
    compile_mobile_release(release)
    publish_mobile_release(release)

    payload = build_latest_mobile_release_payload()

    assert payload["release_version"] == "1.2.3"
    assert payload["build_number"] == 4
    assert payload["status"] == "PUBLISHED"
    assert payload["update_policy"] == "FORCE"
    assert payload["android_download_url"].endswith("/app/downloads/android.apk")


@pytest.mark.django_db
def test_cloudflare_preview_gera_urls_e_ingress():
    preview = build_cloudflare_preview(
        overrides={
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
    )

    assert preview["mode"] == "hybrid"
    assert preview["urls"]["portal_base_url"] == "https://www.mrquentinha.com.br"
    assert preview["urls"]["api_base_url"] == "https://api.mrquentinha.com.br"
    assert any("127.0.0.1:8000" in rule for rule in preview["ingress_rules"])


@pytest.mark.django_db
def test_toggle_cloudflare_ativa_e_restaura_config_local():
    config = ensure_portal_config()
    local_api_base = config.api_base_url
    local_portal_base = config.portal_base_url

    updated_config, _preview_enabled = toggle_cloudflare_mode(
        enabled=True,
        overrides={
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
    )
    assert updated_config.cloudflare_settings["enabled"] is True
    assert updated_config.api_base_url == "https://api.mrquentinha.com.br"
    assert updated_config.portal_base_url == "https://www.mrquentinha.com.br"
    assert "https://www.mrquentinha.com.br" in updated_config.cors_allowed_origins
    assert updated_config.cloudflare_settings["runtime"]["state"] == "active"

    restored_config, _preview_disabled = toggle_cloudflare_mode(enabled=False)
    assert restored_config.cloudflare_settings["enabled"] is False
    assert restored_config.api_base_url == local_api_base
    assert restored_config.portal_base_url == local_portal_base
    assert restored_config.cloudflare_settings["runtime"]["state"] == "inactive"


@pytest.mark.django_db
def test_manage_cloudflare_runtime_rejeita_acao_invalida():
    with pytest.raises(ValidationError):
        manage_cloudflare_runtime(action="invalid-action")

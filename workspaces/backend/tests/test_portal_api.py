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

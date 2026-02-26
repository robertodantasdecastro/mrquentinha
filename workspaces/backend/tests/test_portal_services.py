import pytest

from apps.portal.models import PortalSection
from apps.portal.services import (
    build_public_portal_payload,
    ensure_portal_config,
    save_portal_config,
)


@pytest.mark.django_db
def test_portal_config_singleton():
    first = ensure_portal_config()
    second = ensure_portal_config()

    assert first.id == second.id
    assert first.singleton_key == "default"


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

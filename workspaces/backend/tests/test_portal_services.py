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
            "active_template": "classic",
            "available_templates": [
                {"id": "classic", "label": "Classic"},
                {"id": "letsfit-clean", "label": "LetsFit Clean"},
            ],
        }
    )

    PortalSection.objects.create(
        config=config,
        template_id="classic",
        page="home",
        key="hero",
        title="Hero",
        body_json={"text": "hero"},
        is_enabled=True,
        sort_order=20,
    )
    PortalSection.objects.create(
        config=config,
        template_id="classic",
        page="home",
        key="benefits",
        title="Benefits",
        body_json={"text": "benefits"},
        is_enabled=True,
        sort_order=10,
    )
    PortalSection.objects.create(
        config=config,
        template_id="classic",
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
        template_id="classic",
        page="contato",
        key="other-page",
        title="Other Page",
        body_json={"text": "other-page"},
        is_enabled=True,
        sort_order=2,
    )

    payload = build_public_portal_payload(page="home")

    assert payload["active_template"] == "classic"
    assert [section["key"] for section in payload["sections"]] == [
        "benefits",
        "hero",
    ]

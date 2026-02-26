import hashlib
import json
from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from .models import PortalConfig, PortalPage, PortalSection
from .selectors import get_portal_singleton, list_sections_by_template_page

DEFAULT_TEMPLATE_ITEMS = [
    {"id": "classic", "label": "Classic"},
    {"id": "letsfit-clean", "label": "LetsFit Clean"},
]

DEFAULT_CONFIG_PAYLOAD = {
    "active_template": "classic",
    "available_templates": DEFAULT_TEMPLATE_ITEMS,
    "site_name": "Mr Quentinha",
    "site_title": "Mr Quentinha | Marmitas do dia",
    "meta_description": "Marmitas saudaveis com entrega agendada.",
    "primary_color": "#FF6A00",
    "secondary_color": "#1F2937",
    "dark_bg_color": "#0F172A",
    "android_download_url": "https://www.mrquentinha.com.br/app#android",
    "ios_download_url": "https://www.mrquentinha.com.br/app#ios",
    "qr_target_url": "https://www.mrquentinha.com.br/app",
    "is_published": False,
}

DEFAULT_SECTION_FIXTURES = [
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Comida caseira pronta para o seu dia",
        "sort_order": 10,
        "body_json": {
            "kicker": "Mr Quentinha",
            "headline": "Marmitas equilibradas com entrega planejada",
            "subheadline": "Escolha seu cardapio e receba sem complicacao.",
            "cta_primary": {"label": "Ver cardapio", "href": "/cardapio"},
            "cta_secondary": {"label": "Baixar app", "href": "/app"},
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Por que escolher o Mr Quentinha",
        "sort_order": 20,
        "body_json": {
            "items": [
                "Entrega agendada",
                "Cardapio variado",
                "Preparo padronizado",
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "categories",
        "title": "Categorias",
        "sort_order": 30,
        "body_json": {
            "items": [
                {"name": "Dia a dia", "description": "Praticidade com sabor"},
                {"name": "Fit", "description": "Foco em equilibrio"},
                {"name": "Premium", "description": "Proteina reforcada"},
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "faq",
        "title": "Perguntas frequentes",
        "sort_order": 40,
        "body_json": {
            "items": [
                {
                    "question": "Como faco o pedido?",
                    "answer": "Escolha data, prato e confirme no app ou web.",
                },
                {
                    "question": "Como armazenar?",
                    "answer": "Conserve refrigerado e aqueca quando for consumir.",
                },
            ]
        },
    },
    {
        "template_id": "classic",
        "page": PortalPage.HOME,
        "key": "footer",
        "title": "Atendimento",
        "sort_order": 50,
        "body_json": {
            "phone": "(11) 90000-0000",
            "email": "contato@mrquentinha.com.br",
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "hero",
        "title": "Hero LetsFit",
        "sort_order": 10,
        "body_json": {
            "kicker": "Plano inteligente",
            "headline": "Sua semana organizada com marmitas prontas",
            "subheadline": "Escolha kits e acompanhe seu pedido em tempo real.",
            "background_image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
            "cta_primary": {"label": "Montar kit", "href": "/cardapio"},
            "cta_secondary": {"label": "Como funciona", "href": "/como-funciona"},
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "benefits",
        "title": "Beneficios",
        "sort_order": 20,
        "body_json": {
            "items": [
                {"text": "Pronto em 5 min", "icon": "clock"},
                {"text": "Entrega agendada", "icon": "truck"},
                {"text": "Ingredientes selecionados", "icon": "check"},
                {"text": "Pagamento no app", "icon": "card"},
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "categories",
        "title": "Categorias letsfit",
        "sort_order": 30,
        "body_json": {
            "items": [
                {
                    "name": "Dia a dia",
                    "description": "Comida caseira equilibrada para todos os dias.",
                    "image_url": "https://images.unsplash.com/photo-1546069901-ba9599a7e63c",
                },
                {
                    "name": "Low carb",
                    "description": "Opcao com menos carboidrato e foco em proteina.",
                    "image_url": "https://images.unsplash.com/photo-1603569283847-aa295f0d016a",
                },
                {
                    "name": "Vegetariano",
                    "description": (
                        "Receitas leves com legumes, graos e proteina vegetal."
                    ),
                    "image_url": "https://images.unsplash.com/photo-1512621776951-a57141f2eefd",
                },
                {
                    "name": "Kits semanais",
                    "description": "Pacotes fechados para a semana inteira.",
                    "image_url": "https://images.unsplash.com/photo-1579113800032-c38bd7635818",
                },
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "kit",
        "title": "Monte seu kit",
        "sort_order": 40,
        "body_json": {
            "kicker": "Nao sabe o que escolher?",
            "headline": "Monte seu kit para a semana",
            "description": (
                "Selecione dias e objetivo. "
                "O sistema sugere combinacoes do cardapio do dia."
            ),
            "cta_label": "Simular kit personalizado",
            "cta_href": "/cardapio",
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "how_to_heat",
        "title": "Conservacao e aquecimento",
        "sort_order": 45,
        "body_json": {
            "title": "Facil de preparar e armazenar",
            "subheadline": "As embalagens vao do freezer ao micro-ondas com seguranca.",
            "cards": [
                {
                    "tone": "cold",
                    "title": "Conservacao",
                    "description": (
                        "Geladeira por ate 3 dias ou freezer por ate 30 dias."
                    ),
                },
                {
                    "tone": "hot",
                    "title": "Aquecimento",
                    "description": (
                        "No micro-ondas por 5 a 7 minutos "
                        "apos abrir um respiro na embalagem."
                    ),
                },
            ],
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "faq",
        "title": "FAQ",
        "sort_order": 50,
        "body_json": {
            "items": [
                {
                    "question": "Como agendar a entrega?",
                    "answer": "No checkout, selecione a data de entrega disponivel.",
                },
                {
                    "question": "Aceita VR/VA?",
                    "answer": (
                        "Aceitamos VR e VA conforme rede habilitada no pagamento."
                    ),
                },
                {
                    "question": "A comida chega congelada?",
                    "answer": (
                        "Voce escolhe entre entrega fresca para o dia "
                        "ou ultracongelada."
                    ),
                },
            ]
        },
    },
    {
        "template_id": "letsfit-clean",
        "page": PortalPage.HOME,
        "key": "footer",
        "title": "Contato",
        "sort_order": 60,
        "body_json": {
            "phone": "(11) 90000-0000",
            "email": "atendimento@mrquentinha.com.br",
        },
    },
]


CONFIG_MUTABLE_FIELDS = [
    "active_template",
    "available_templates",
    "site_name",
    "site_title",
    "meta_description",
    "primary_color",
    "secondary_color",
    "dark_bg_color",
    "android_download_url",
    "ios_download_url",
    "qr_target_url",
    "is_published",
    "published_at",
]


def _extract_template_ids(available_templates: list) -> set[str]:
    template_ids: set[str] = set()

    for item in available_templates:
        if isinstance(item, dict):
            template_id = str(item.get("id", "")).strip()
        else:
            template_id = str(item).strip()

        if template_id:
            template_ids.add(template_id)

    return template_ids


def _seed_sections_if_empty(config: PortalConfig) -> None:
    if PortalSection.objects.filter(config=config).exists():
        return

    for fixture in DEFAULT_SECTION_FIXTURES:
        PortalSection.objects.create(
            config=config,
            template_id=fixture["template_id"],
            page=fixture["page"],
            key=fixture["key"],
            title=fixture["title"],
            body_json=fixture["body_json"],
            is_enabled=True,
            sort_order=fixture["sort_order"],
        )


def ensure_portal_config() -> PortalConfig:
    config = get_portal_singleton()
    if config is not None:
        _seed_sections_if_empty(config)
        return config

    config = PortalConfig.objects.create(
        singleton_key=PortalConfig.SINGLETON_KEY,
        **DEFAULT_CONFIG_PAYLOAD,
    )
    _seed_sections_if_empty(config)
    return config


@transaction.atomic
def save_portal_config(
    *,
    payload: dict,
    instance: PortalConfig | None = None,
) -> tuple[PortalConfig, bool]:
    config = instance or get_portal_singleton()
    created = False

    if config is None:
        config = PortalConfig(
            singleton_key=PortalConfig.SINGLETON_KEY,
            **DEFAULT_CONFIG_PAYLOAD,
        )
        created = True

    update_fields: list[str] = []
    for field_name in CONFIG_MUTABLE_FIELDS:
        if field_name not in payload:
            continue

        new_value = payload[field_name]
        if getattr(config, field_name) == new_value:
            continue

        setattr(config, field_name, new_value)
        update_fields.append(field_name)

    available_templates = payload.get("available_templates", config.available_templates)
    active_template = payload.get("active_template", config.active_template)

    if available_templates and active_template not in _extract_template_ids(
        available_templates
    ):
        raise ValidationError("active_template precisa existir em available_templates.")

    if created:
        config.save()
        return config, True

    if update_fields:
        update_fields.append("updated_at")
        config.save(update_fields=update_fields)

    return config, False


@transaction.atomic
def publish_portal_config() -> PortalConfig:
    config = ensure_portal_config()
    now = timezone.now()

    update_fields: list[str] = []
    if not config.is_published:
        config.is_published = True
        update_fields.append("is_published")

    if config.published_at is None:
        config.published_at = now
        update_fields.append("published_at")

    if update_fields:
        update_fields.append("updated_at")
        config.save(update_fields=update_fields)

    return config


def _resolve_templates(config: PortalConfig) -> list[dict]:
    if config.available_templates:
        return config.available_templates

    template_ids = (
        PortalSection.objects.filter(config=config)
        .values_list("template_id", flat=True)
        .distinct()
        .order_by("template_id")
    )
    return [
        {"id": template_id, "label": template_id.title()}
        for template_id in template_ids
    ]


def build_public_portal_payload(*, page: str = PortalPage.HOME) -> dict:
    config = ensure_portal_config()
    sections = list_sections_by_template_page(
        config=config,
        template_id=config.active_template,
        page=page,
        enabled_only=True,
    )

    return {
        "active_template": config.active_template,
        "available_templates": _resolve_templates(config),
        "site_name": config.site_name,
        "site_title": config.site_title,
        "meta_description": config.meta_description,
        "primary_color": config.primary_color,
        "secondary_color": config.secondary_color,
        "dark_bg_color": config.dark_bg_color,
        "android_download_url": config.android_download_url,
        "ios_download_url": config.ios_download_url,
        "qr_target_url": config.qr_target_url,
        "is_published": config.is_published,
        "updated_at": config.updated_at,
        "page": page,
        "sections": [
            {
                "id": section.id,
                "template_id": section.template_id,
                "page": section.page,
                "key": section.key,
                "title": section.title,
                "body_json": section.body_json,
                "sort_order": section.sort_order,
                "updated_at": section.updated_at,
            }
            for section in sections
        ],
    }


def _serialize_dt(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.isoformat()


def build_portal_version_payload() -> dict:
    config = ensure_portal_config()
    sections_qs = PortalSection.objects.filter(
        config=config, template_id=config.active_template
    )

    latest_section = sections_qs.aggregate(latest=Max("updated_at"))["latest"]
    timestamps = [ts for ts in [config.updated_at, latest_section] if ts is not None]
    resolved_updated_at = max(timestamps) if timestamps else config.updated_at

    fingerprint_payload = {
        "active_template": config.active_template,
        "config_updated_at": _serialize_dt(config.updated_at),
        "sections": [
            {
                "id": row["id"],
                "updated_at": _serialize_dt(row["updated_at"]),
            }
            for row in sections_qs.order_by("id").values("id", "updated_at")
        ],
    }
    digest = hashlib.sha256(
        json.dumps(fingerprint_payload, sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "updated_at": _serialize_dt(resolved_updated_at),
        "hash": digest,
        "etag": digest,
    }


@transaction.atomic
def seed_portal_defaults() -> dict:
    config, created = save_portal_config(payload=DEFAULT_CONFIG_PAYLOAD)
    created_sections = 0
    updated_sections = 0

    for fixture in DEFAULT_SECTION_FIXTURES:
        defaults = {
            "title": fixture["title"],
            "body_json": fixture["body_json"],
            "is_enabled": True,
            "sort_order": fixture["sort_order"],
        }
        section, section_created = PortalSection.objects.update_or_create(
            config=config,
            template_id=fixture["template_id"],
            page=fixture["page"],
            key=fixture["key"],
            defaults=defaults,
        )

        if section_created:
            created_sections += 1
        else:
            updated_sections += 1

    return {
        "config_created": created,
        "config_id": config.id,
        "sections_created": created_sections,
        "sections_updated": updated_sections,
    }

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from html import escape
from urllib.parse import quote, urlparse, urlunparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import EmailMultiAlternatives
from django.db import transaction
from django.utils import timezone

from .models import (
    Role,
    UserAdminModulePermission,
    UserProfile,
    UserRole,
    UserTask,
    UserTaskAssignment,
    UserTaskCategory,
)


class SystemRole:
    ADMIN = "ADMIN"
    FINANCEIRO = "FINANCEIRO"
    COZINHA = "COZINHA"
    COMPRAS = "COMPRAS"
    ESTOQUE = "ESTOQUE"
    CLIENTE = "CLIENTE"

    ALL = (ADMIN, FINANCEIRO, COZINHA, COMPRAS, ESTOQUE, CLIENTE)


DEFAULT_ROLE_METADATA = {
    SystemRole.ADMIN: {
        "name": "Administrador",
        "description": "Acesso total ao sistema.",
    },
    SystemRole.FINANCEIRO: {
        "name": "Financeiro",
        "description": "Gestao financeira, caixa e relatorios.",
    },
    SystemRole.COZINHA: {
        "name": "Cozinha",
        "description": "Operacao de cardapio e producao.",
    },
    SystemRole.COMPRAS: {
        "name": "Compras",
        "description": "Gestao de compras e suprimentos.",
    },
    SystemRole.ESTOQUE: {
        "name": "Estoque",
        "description": "Movimentacao e controle de estoque.",
    },
    SystemRole.CLIENTE: {
        "name": "Cliente",
        "description": "Usuario final para pedidos.",
    },
}

ADMIN_WEB_MODULE_SLUGS = {
    "fluxo-operacional",
    "pedidos",
    "financeiro",
    "estoque",
    "cardapio",
    "compras",
    "producao",
    "usuarios-rbac",
    "clientes",
    "relatorios",
    "portal",
    "auditoria-atividade",
    "administracao-servidor",
    "instalacao-deploy",
    "monitoramento",
}
TECHNICAL_ADMIN_MODULE_SLUGS = {
    "usuarios-rbac",
    "portal",
    "auditoria-atividade",
    "administracao-servidor",
    "instalacao-deploy",
}
ROLE_ADMIN_MODULE_ACCESS = {
    SystemRole.ADMIN: set(ADMIN_WEB_MODULE_SLUGS),
    SystemRole.FINANCEIRO: {
        "fluxo-operacional",
        "pedidos",
        "financeiro",
        "clientes",
        "relatorios",
        "monitoramento",
    },
    SystemRole.COZINHA: {
        "fluxo-operacional",
        "cardapio",
        "producao",
        "pedidos",
        "estoque",
        "compras",
        "clientes",
        "monitoramento",
    },
    SystemRole.COMPRAS: {
        "fluxo-operacional",
        "compras",
        "estoque",
        "producao",
        "pedidos",
        "clientes",
        "monitoramento",
        "relatorios",
    },
    SystemRole.ESTOQUE: {
        "fluxo-operacional",
        "estoque",
        "compras",
        "producao",
        "pedidos",
        "monitoramento",
    },
    SystemRole.CLIENTE: set(),
}

DEFAULT_TASK_CATEGORY_METADATA = {
    "OPERACAO_PRODUCAO": {
        "name": "Operacao de producao",
        "description": "Execucao de cozinha, preparo e controle operacional.",
        "technical_scope": False,
    },
    "SUPRIMENTOS_LOGISTICA": {
        "name": "Suprimentos e logistica",
        "description": "Compras, estoque e abastecimento.",
        "technical_scope": False,
    },
    "FINANCEIRO_CONTROLADORIA": {
        "name": "Financeiro e controladoria",
        "description": "Caixa, contas e acompanhamento de resultados.",
        "technical_scope": False,
    },
    "ATENDIMENTO_CLIENTE": {
        "name": "Atendimento e pedidos",
        "description": "Relacionamento com clientes e operacao de pedidos.",
        "technical_scope": False,
    },
    "ADMINISTRACAO_TECNICA": {
        "name": "Administracao tecnica",
        "description": "Portal, servidor, deploy e configuracoes da plataforma.",
        "technical_scope": True,
    },
}

DEFAULT_TASK_METADATA = {
    "PRODUCAO_PLANEJAMENTO": {
        "category_code": "OPERACAO_PRODUCAO",
        "name": "Planejamento de producao",
        "description": "Planeja lotes, cronograma e capacidade diaria.",
        "technical_scope": False,
        "related_module_slug": "producao",
    },
    "PRODUCAO_EXECUCAO": {
        "category_code": "OPERACAO_PRODUCAO",
        "name": "Execucao de cozinha",
        "description": "Executa preparo e controla etapas de producao.",
        "technical_scope": False,
        "related_module_slug": "producao",
    },
    "ESTOQUE_OPERACAO": {
        "category_code": "SUPRIMENTOS_LOGISTICA",
        "name": "Operacao de estoque",
        "description": "Controla entradas, saidas e ajustes de inventario.",
        "technical_scope": False,
        "related_module_slug": "estoque",
    },
    "COMPRAS_ABASTECIMENTO": {
        "category_code": "SUPRIMENTOS_LOGISTICA",
        "name": "Compras e abastecimento",
        "description": "Gera requisicoes e acompanha compras.",
        "technical_scope": False,
        "related_module_slug": "compras",
    },
    "FINANCEIRO_CAIXA": {
        "category_code": "FINANCEIRO_CONTROLADORIA",
        "name": "Caixa e conciliacao",
        "description": "Opera fluxo de caixa, conciliacao e pagamentos.",
        "technical_scope": False,
        "related_module_slug": "financeiro",
    },
    "FINANCEIRO_RELATORIOS": {
        "category_code": "FINANCEIRO_CONTROLADORIA",
        "name": "Relatorios gerenciais",
        "description": "Analisa indicadores e resultados financeiros.",
        "technical_scope": False,
        "related_module_slug": "relatorios",
    },
    "PEDIDOS_ATENDIMENTO": {
        "category_code": "ATENDIMENTO_CLIENTE",
        "name": "Atendimento de pedidos",
        "description": "Acompanha pedidos e atendimento ao cliente.",
        "technical_scope": False,
        "related_module_slug": "pedidos",
    },
    "CLIENTES_GESTAO": {
        "category_code": "ATENDIMENTO_CLIENTE",
        "name": "Gestao de clientes",
        "description": "Gerencia cadastro, status e governanca de clientes.",
        "technical_scope": False,
        "related_module_slug": "clientes",
    },
    "PORTAL_CMS_ADMIN": {
        "category_code": "ADMINISTRACAO_TECNICA",
        "name": "Administracao do Portal CMS",
        "description": "Configura templates, autenticacao social e publicacao.",
        "technical_scope": True,
        "related_module_slug": "portal",
    },
    "SERVIDOR_ADMIN": {
        "category_code": "ADMINISTRACAO_TECNICA",
        "name": "Administracao de servidor",
        "description": "Configura conectividade, DNS e servicos do servidor.",
        "technical_scope": True,
        "related_module_slug": "administracao-servidor",
    },
    "DEPLOY_RELEASE": {
        "category_code": "ADMINISTRACAO_TECNICA",
        "name": "Instalacao e deploy",
        "description": "Opera assistente de instalacao e releases.",
        "technical_scope": True,
        "related_module_slug": "instalacao-deploy",
    },
}

DEFAULT_CLIENT_BASE_URL = "http://127.0.0.1:3001"
EMAIL_VERIFICATION_TOKEN_TTL_HOURS = 3

ESSENTIAL_PROFILE_FIELDS = (
    "full_name",
    "phone",
    "postal_code",
    "street",
    "street_number",
    "neighborhood",
    "city",
    "state",
)


def _normalize_url(value: str) -> str:
    raw_value = str(value or "").strip().rstrip("/")
    if not raw_value:
        return ""
    parsed = urlparse(raw_value)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return ""
    return urlunparse((parsed.scheme, parsed.netloc, "", "", "", "")).rstrip("/")


def resolve_client_base_url(*, preferred_base_url: str = "") -> str:
    candidate = _normalize_url(preferred_base_url)
    if candidate:
        return candidate

    try:
        from apps.portal.services import ensure_portal_config

        portal_config = ensure_portal_config()
        from_config = _normalize_url(str(portal_config.client_base_url or ""))
        if from_config:
            return from_config
    except Exception:
        pass

    return DEFAULT_CLIENT_BASE_URL


def _hash_email_verification_token(token: str) -> str:
    payload = f"{settings.SECRET_KEY}:{token}".encode()
    return hashlib.sha256(payload).hexdigest()


def _build_email_verification_link(*, token: str, client_base_url: str) -> str:
    return f"{client_base_url}/conta/confirmar-email?token={quote(token)}"


def _build_company_email_context(*, client_base_url: str) -> dict:
    context = {
        "site_name": "Mr Quentinha",
        "primary_color": "#FF6A00",
        "support_email": "contato@mrquentinha.com.br",
        "support_phone": "",
        "site_url": client_base_url,
        "logo_url": f"{client_base_url}/brand/png/logo_wordmark_2000x.png",
    }
    try:
        from apps.portal.models import PortalPage
        from apps.portal.selectors import list_sections_by_template_page
        from apps.portal.services import ensure_portal_config

        portal_config = ensure_portal_config()
        if str(portal_config.site_name or "").strip():
            context["site_name"] = str(portal_config.site_name).strip()
        if str(portal_config.primary_color or "").strip():
            context["primary_color"] = str(portal_config.primary_color).strip()

        footer_section = (
            list_sections_by_template_page(
                config=portal_config,
                template_id=portal_config.client_active_template,
                page=PortalPage.HOME,
                enabled_only=False,
            )
            .filter(key="footer")
            .first()
        )
        if footer_section is not None and isinstance(footer_section.body_json, dict):
            support_email = str(footer_section.body_json.get("email", "")).strip()
            support_phone = str(footer_section.body_json.get("phone", "")).strip()
            if support_email:
                context["support_email"] = support_email
            if support_phone:
                context["support_phone"] = support_phone
    except Exception:
        pass

    return context


def _build_email_verification_html_body(
    *,
    username: str,
    confirmation_link: str,
    token_ttl_hours: int,
    client_base_url: str,
) -> str:
    company = _build_company_email_context(client_base_url=client_base_url)
    site_name = escape(company["site_name"])
    support_email = escape(company["support_email"])
    support_phone = escape(company["support_phone"])
    logo_url = escape(company["logo_url"])
    primary_color = escape(company["primary_color"])
    site_url = escape(company["site_url"])
    safe_username = escape(username)
    safe_link = escape(confirmation_link)
    year = timezone.localtime().year

    support_phone_html = (
        f"<p style='margin:4px 0;color:#475569;'>Telefone: {support_phone}</p>"
        if support_phone
        else ""
    )

    return f"""
<!doctype html>
<html lang="pt-BR">
<body
  style="
    margin:0;
    padding:0;
    background:#f8fafc;
    font-family:Arial,sans-serif;
  "
>
  <table
    width="100%"
    cellpadding="0"
    cellspacing="0"
    style="background:#f8fafc;padding:24px 0;"
  >
    <tr>
      <td align="center">
        <table
          width="100%"
          cellpadding="0"
          cellspacing="0"
          style="
            max-width:640px;
            background:#ffffff;
            border:1px solid #e2e8f0;
            border-radius:16px;
            overflow:hidden;
          "
        >
          <tr>
            <td style="padding:24px 24px 12px 24px;text-align:center;">
              <img
                src="{logo_url}"
                alt="{site_name}"
                style="max-width:220px;height:auto;display:inline-block;"
              />
            </td>
          </tr>
          <tr>
            <td style="padding:0 24px 20px 24px;">
              <h1
                style="margin:0 0 12px 0;font-size:22px;line-height:1.3;color:#0f172a;"
              >
                Confirme seu e-mail, {safe_username}
              </h1>
              <p
                style="margin:0 0 12px 0;color:#334155;font-size:15px;line-height:1.5;"
              >
                Seu cadastro no <strong>{site_name}</strong> foi criado com sucesso.
                Para liberar o acesso ao login e aos recursos de pagamento,
                confirme seu e-mail.
              </p>
              <p
                style="margin:0 0 20px 0;color:#334155;font-size:15px;line-height:1.5;"
              >
                Este link expira em <strong>{token_ttl_hours} horas</strong>.
              </p>
              <p style="margin:0 0 24px 0;text-align:center;">
                <a
                  href="{safe_link}"
                  style="
                    display:inline-block;
                    background:{primary_color};
                    color:#ffffff;
                    text-decoration:none;
                    font-weight:700;
                    padding:12px 20px;
                    border-radius:10px;
                  "
                >
                  Confirmar e-mail
                </a>
              </p>
              <p style="margin:0 0 8px 0;color:#64748b;font-size:13px;line-height:1.5;">
                Se o botão não abrir, copie e cole o link no navegador:
              </p>
              <p
                style="
                  margin:0 0 16px 0;
                  color:#0f172a;
                  font-size:13px;
                  line-height:1.5;
                  word-break:break-all;
                "
              >
                {safe_link}
              </p>
              <hr style="border:none;border-top:1px solid #e2e8f0;margin:16px 0;" />
              <p style="margin:4px 0;color:#475569;">{site_name}</p>
              <p style="margin:4px 0;color:#475569;">E-mail: {support_email}</p>
              {support_phone_html}
              <p style="margin:4px 0;color:#475569;">Site: {site_url}</p>
            </td>
          </tr>
          <tr>
            <td
              style="
                padding:12px 24px 24px 24px;
                text-align:center;
                color:#94a3b8;
                font-size:12px;
              "
            >
              © {year} {site_name}. Todos os direitos reservados.
            </td>
          </tr>
        </table>
      </td>
    </tr>
  </table>
</body>
</html>
""".strip()


def _collect_missing_essential_profile_fields(user) -> list[str]:
    missing: list[str] = []
    email_value = str(getattr(user, "email", "") or "").strip()
    if not email_value:
        missing.append("email")

    profile = getattr(user, "profile", None)
    if profile is None:
        missing.extend(ESSENTIAL_PROFILE_FIELDS)
        missing.append("cpf_ou_cnpj")
        missing.append("email_verificado")
        return missing

    for field_name in ESSENTIAL_PROFILE_FIELDS:
        if str(getattr(profile, field_name, "") or "").strip():
            continue
        missing.append(field_name)

    cpf_value = str(getattr(profile, "cpf", "") or "").strip()
    cnpj_value = str(getattr(profile, "cnpj", "") or "").strip()
    if not cpf_value and not cnpj_value:
        missing.append("cpf_ou_cnpj")

    if not getattr(profile, "email_verified_at", None):
        missing.append("email_verificado")

    return missing


def build_user_account_compliance(user) -> dict:
    missing_fields = _collect_missing_essential_profile_fields(user)
    profile = getattr(user, "profile", None)

    return {
        "email_verified": bool(profile and profile.email_verified_at),
        "email_verified_at": profile.email_verified_at if profile else None,
        "email_verification_last_sent_at": (
            profile.email_verification_last_sent_at if profile else None
        ),
        "essential_profile_complete": len(missing_fields) == 0,
        "missing_essential_profile_fields": missing_fields,
    }


@transaction.atomic
def issue_email_verification_for_user(
    *,
    user,
    preferred_client_base_url: str = "",
) -> dict:
    email_value = str(getattr(user, "email", "") or "").strip()
    if not email_value:
        return {
            "sent": False,
            "detail": "Usuario sem e-mail. Confirmacao nao enviada.",
            "client_base_url": resolve_client_base_url(
                preferred_base_url=preferred_client_base_url
            ),
        }

    profile, _created = UserProfile.objects.get_or_create(user=user)
    if profile.email_verified_at:
        return {
            "sent": False,
            "detail": "E-mail ja confirmado para este usuario.",
            "client_base_url": resolve_client_base_url(
                preferred_base_url=preferred_client_base_url
            ),
        }

    client_base_url = resolve_client_base_url(
        preferred_base_url=preferred_client_base_url
    )
    token = secrets.token_urlsafe(48)
    now = timezone.now()

    profile.email_verification_token_hash = _hash_email_verification_token(token)
    profile.email_verification_token_created_at = now
    profile.email_verification_last_sent_at = now
    profile.email_verification_last_client_base_url = client_base_url
    profile.save(
        update_fields=[
            "email_verification_token_hash",
            "email_verification_token_created_at",
            "email_verification_last_sent_at",
            "email_verification_last_client_base_url",
            "updated_at",
        ]
    )

    confirmation_link = _build_email_verification_link(
        token=token,
        client_base_url=client_base_url,
    )
    token_ttl_hours = int(
        getattr(
            settings,
            "ACCOUNTS_EMAIL_VERIFICATION_TOKEN_TTL_HOURS",
            EMAIL_VERIFICATION_TOKEN_TTL_HOURS,
        )
    )
    subject = "[Mr Quentinha] Confirme seu e-mail"
    text_body = "\n".join(
        [
            f"Ola, {user.username}!",
            "",
            "Recebemos seu cadastro no Mr Quentinha.",
            (
                "Confirme seu e-mail para habilitar autenticacao "
                "e pagamentos com seguranca."
            ),
            "",
            f"Link de confirmacao: {confirmation_link}",
            f"Validade: {token_ttl_hours} horas.",
            "",
            "Se voce nao reconhece este cadastro, ignore este e-mail.",
        ]
    )
    html_body = _build_email_verification_html_body(
        username=user.username,
        confirmation_link=confirmation_link,
        token_ttl_hours=token_ttl_hours,
        client_base_url=client_base_url,
    )
    from_email = (
        str(getattr(settings, "DEFAULT_FROM_EMAIL", "")).strip()
        or "noreply@mrquentinha.local"
    )
    reply_to: list[str] = []
    connection = None
    try:
        from apps.portal.services import resolve_portal_email_delivery_options

        delivery_options = resolve_portal_email_delivery_options()
        from_email = str(delivery_options.get("from_email", "")).strip() or from_email
        reply_to = list(delivery_options.get("reply_to", []))
        connection = delivery_options.get("connection")
    except Exception:
        # Fallback silencioso para backend padrão quando a configuração SMTP do portal
        # estiver ausente ou inválida.
        connection = None

    email_message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=from_email,
        to=[email_value],
        reply_to=reply_to or None,
        connection=connection,
    )
    email_message.attach_alternative(html_body, "text/html")
    sent_count = email_message.send(fail_silently=True)

    return {
        "sent": bool(sent_count),
        "detail": (
            "E-mail de confirmacao enviado."
            if sent_count
            else "Nao foi possivel enviar o e-mail de confirmacao."
        ),
        "email": email_value,
        "client_base_url": client_base_url,
    }


@transaction.atomic
def confirm_email_verification_token(*, token: str):
    clean_token = str(token or "").strip()
    if not clean_token:
        raise ValidationError("Token de confirmacao nao informado.")

    token_hash = _hash_email_verification_token(clean_token)
    profile = (
        UserProfile.objects.select_related("user")
        .filter(email_verification_token_hash=token_hash)
        .first()
    )
    if profile is None:
        raise ValidationError("Token de confirmacao invalido.")

    created_at = profile.email_verification_token_created_at
    if created_at is None:
        raise ValidationError("Token de confirmacao invalido.")

    ttl_hours = int(
        getattr(
            settings,
            "ACCOUNTS_EMAIL_VERIFICATION_TOKEN_TTL_HOURS",
            EMAIL_VERIFICATION_TOKEN_TTL_HOURS,
        )
    )
    expires_at = created_at + timedelta(hours=ttl_hours)
    if timezone.now() > expires_at:
        profile.email_verification_token_hash = ""
        profile.email_verification_token_created_at = None
        profile.save(
            update_fields=[
                "email_verification_token_hash",
                "email_verification_token_created_at",
                "updated_at",
            ]
        )
        raise ValidationError("Token de confirmacao expirado. Solicite novo e-mail.")

    now = timezone.now()
    profile.email_verified_at = now
    profile.email_verification_token_hash = ""
    profile.email_verification_token_created_at = None
    profile.save(
        update_fields=[
            "email_verified_at",
            "email_verification_token_hash",
            "email_verification_token_created_at",
            "updated_at",
        ]
    )

    return profile.user


def ensure_default_roles() -> dict[str, Role]:
    roles: dict[str, Role] = {}

    for code, metadata in DEFAULT_ROLE_METADATA.items():
        role, _ = Role.objects.get_or_create(
            code=code,
            defaults={
                "name": metadata["name"],
                "description": metadata["description"],
                "is_active": True,
            },
        )

        updates: list[str] = []
        if role.name != metadata["name"]:
            role.name = metadata["name"]
            updates.append("name")
        if role.description != metadata["description"]:
            role.description = metadata["description"]
            updates.append("description")
        if not role.is_active:
            role.is_active = True
            updates.append("is_active")

        if updates:
            updates.append("updated_at")
            role.save(update_fields=updates)

        roles[code] = role

    return roles


def ensure_default_task_catalog() -> (
    tuple[dict[str, UserTaskCategory], dict[str, UserTask]]
):
    categories: dict[str, UserTaskCategory] = {}
    tasks: dict[str, UserTask] = {}

    for code, metadata in DEFAULT_TASK_CATEGORY_METADATA.items():
        category, _ = UserTaskCategory.objects.get_or_create(
            code=code,
            defaults={
                "name": metadata["name"],
                "description": metadata["description"],
                "is_active": True,
                "technical_scope": bool(metadata["technical_scope"]),
            },
        )

        updates: list[str] = []
        if category.name != metadata["name"]:
            category.name = metadata["name"]
            updates.append("name")
        if category.description != metadata["description"]:
            category.description = metadata["description"]
            updates.append("description")
        if category.technical_scope != bool(metadata["technical_scope"]):
            category.technical_scope = bool(metadata["technical_scope"])
            updates.append("technical_scope")
        if not category.is_active:
            category.is_active = True
            updates.append("is_active")

        if updates:
            updates.append("updated_at")
            category.save(update_fields=updates)

        categories[code] = category

    for code, metadata in DEFAULT_TASK_METADATA.items():
        category_code = str(metadata["category_code"])
        category = categories[category_code]
        related_module_slug = str(metadata.get("related_module_slug", "")).strip()
        task, _ = UserTask.objects.get_or_create(
            code=code,
            defaults={
                "category": category,
                "name": metadata["name"],
                "description": metadata["description"],
                "is_active": True,
                "technical_scope": bool(metadata["technical_scope"]),
                "related_module_slug": related_module_slug,
            },
        )

        updates: list[str] = []
        if task.category_id != category.id:
            task.category = category
            updates.append("category")
        if task.name != metadata["name"]:
            task.name = metadata["name"]
            updates.append("name")
        if task.description != metadata["description"]:
            task.description = metadata["description"]
            updates.append("description")
        if task.technical_scope != bool(metadata["technical_scope"]):
            task.technical_scope = bool(metadata["technical_scope"])
            updates.append("technical_scope")
        if task.related_module_slug != related_module_slug:
            task.related_module_slug = related_module_slug
            updates.append("related_module_slug")
        if not task.is_active:
            task.is_active = True
            updates.append("is_active")

        if updates:
            updates.append("updated_at")
            task.save(update_fields=updates)

        tasks[code] = task

    return categories, tasks


@transaction.atomic
def assign_roles_to_user(
    *,
    user,
    role_codes: list[str],
    replace: bool = True,
) -> list[str]:
    if not user or not getattr(user, "pk", None):
        raise ValidationError("Usuario invalido para atribuicao de papeis.")

    if not role_codes:
        raise ValidationError("Informe ao menos um papel para atribuicao.")

    normalized_codes = sorted({code.strip().upper() for code in role_codes if code})
    invalid_codes = [code for code in normalized_codes if code not in SystemRole.ALL]
    if invalid_codes:
        raise ValidationError(f"Papeis invalidos: {', '.join(invalid_codes)}")

    roles = ensure_default_roles()

    if replace:
        UserRole.objects.filter(user=user).exclude(
            role__code__in=normalized_codes
        ).delete()

    for code in normalized_codes:
        UserRole.objects.get_or_create(user=user, role=roles[code])

    if hasattr(user, "_rbac_role_codes"):
        delattr(user, "_rbac_role_codes")

    return normalized_codes


@transaction.atomic
def assign_tasks_to_user(
    *,
    user,
    task_codes: list[str],
    replace: bool = True,
    assigned_by=None,
) -> list[str]:
    if not user or not getattr(user, "pk", None):
        raise ValidationError("Usuario invalido para atribuicao de tarefas.")

    ensure_default_task_catalog()
    normalized_codes = sorted(
        {str(code or "").strip().upper() for code in task_codes if code}
    )

    available_codes = set(
        UserTask.objects.filter(is_active=True).values_list("code", flat=True)
    )
    invalid_codes = [code for code in normalized_codes if code not in available_codes]
    if invalid_codes:
        raise ValidationError(f"Tarefas invalidas: {', '.join(invalid_codes)}")

    if replace:
        UserTaskAssignment.objects.filter(user=user).exclude(
            task__code__in=normalized_codes
        ).delete()

    if normalized_codes:
        task_map = {
            task.code: task
            for task in UserTask.objects.filter(
                code__in=normalized_codes
            ).select_related("category")
        }
        for code in normalized_codes:
            UserTaskAssignment.objects.get_or_create(
                user=user,
                task=task_map[code],
                defaults={"assigned_by": assigned_by},
            )

    if hasattr(user, "_rbac_task_codes"):
        delattr(user, "_rbac_task_codes")
    if hasattr(user, "_rbac_task_category_codes"):
        delattr(user, "_rbac_task_category_codes")

    return normalized_codes


def get_user_role_codes(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    if getattr(user, "is_superuser", False):
        return {SystemRole.ADMIN}

    cached_codes = getattr(user, "_rbac_role_codes", None)
    if cached_codes is not None:
        return cached_codes

    role_codes = set(
        UserRole.objects.filter(user=user, role__is_active=True).values_list(
            "role__code", flat=True
        )
    )
    user._rbac_role_codes = role_codes
    return role_codes


def get_user_task_codes(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    cached_codes = getattr(user, "_rbac_task_codes", None)
    if cached_codes is not None:
        return cached_codes

    ensure_default_task_catalog()
    task_codes = set(
        UserTaskAssignment.objects.filter(user=user, task__is_active=True).values_list(
            "task__code", flat=True
        )
    )
    user._rbac_task_codes = task_codes
    return task_codes


def get_user_task_category_codes(user) -> set[str]:
    if not user or not getattr(user, "is_authenticated", False):
        return set()

    cached_codes = getattr(user, "_rbac_task_category_codes", None)
    if cached_codes is not None:
        return cached_codes

    ensure_default_task_catalog()
    category_codes = set(
        UserTaskAssignment.objects.filter(user=user, task__is_active=True).values_list(
            "task__category__code", flat=True
        )
    )
    user._rbac_task_category_codes = category_codes
    return category_codes


def get_allowed_admin_module_slugs(user) -> list[str]:
    return sorted(get_user_admin_module_access_map(user).keys())


def _has_base_technical_admin_access(user) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False) or getattr(user, "is_staff", False):
        return True

    return SystemRole.ADMIN in get_user_role_codes(user)


def get_user_admin_module_access_map(user) -> dict[str, str]:
    if not user or not getattr(user, "is_authenticated", False):
        return {}

    cached = getattr(user, "_rbac_admin_module_access_map", None)
    if isinstance(cached, dict):
        return cached

    if _has_base_technical_admin_access(user):
        full_access = {module_slug: "write" for module_slug in ADMIN_WEB_MODULE_SLUGS}
        user._rbac_admin_module_access_map = full_access
        return full_access

    explicit_permissions_qs = UserAdminModulePermission.objects.filter(user=user).values(
        "module_slug",
        "access_level",
    )
    explicit_permissions = list(explicit_permissions_qs)
    if explicit_permissions:
        explicit_access: dict[str, str] = {}
        for permission in explicit_permissions:
            module_slug = str(permission["module_slug"] or "").strip()
            access_level = str(permission["access_level"] or "").strip().lower()
            if module_slug not in ADMIN_WEB_MODULE_SLUGS:
                continue
            if module_slug in TECHNICAL_ADMIN_MODULE_SLUGS:
                continue
            explicit_access[module_slug] = "write" if access_level == "write" else "read"
        user._rbac_admin_module_access_map = explicit_access
        return explicit_access

    role_codes = get_user_role_codes(user)
    role_access_map: dict[str, str] = {}
    for role_code in role_codes:
        for module_slug in ROLE_ADMIN_MODULE_ACCESS.get(role_code, set()):
            if module_slug in TECHNICAL_ADMIN_MODULE_SLUGS:
                continue
            role_access_map[module_slug] = "write"

    user._rbac_admin_module_access_map = role_access_map
    return role_access_map


def get_user_admin_module_permissions(user) -> list[dict[str, str]]:
    access_map = get_user_admin_module_access_map(user)
    return [
        {"module_slug": module_slug, "access_level": access_map[module_slug]}
        for module_slug in sorted(access_map.keys())
    ]


@transaction.atomic
def assign_admin_modules_to_user(
    *,
    user,
    module_permissions: list[dict[str, str]],
    replace: bool = True,
    assigned_by=None,
) -> dict[str, str]:
    if not user:
        raise ValidationError("Usuario invalido para atribuicao de modulos.")

    normalized_permissions: dict[str, str] = {}
    for entry in module_permissions:
        module_slug = str(entry.get("module_slug", "") or "").strip()
        access_level = str(entry.get("access_level", "") or "").strip().lower()
        if not module_slug:
            continue
        if module_slug not in ADMIN_WEB_MODULE_SLUGS:
            raise ValidationError(f"Modulo admin invalido: {module_slug}.")
        if module_slug in TECHNICAL_ADMIN_MODULE_SLUGS:
            raise ValidationError(
                "Modulos tecnicos exigem papel ADMIN e nao podem ser delegados por permissao granular."
            )
        normalized_permissions[module_slug] = "write" if access_level == "write" else "read"

    if replace:
        UserAdminModulePermission.objects.filter(user=user).delete()

    existing_by_module = {
        item.module_slug: item
        for item in UserAdminModulePermission.objects.filter(user=user)
    }
    to_create: list[UserAdminModulePermission] = []
    to_update: list[UserAdminModulePermission] = []
    for module_slug, access_level in normalized_permissions.items():
        existing = existing_by_module.get(module_slug)
        if existing is None:
            to_create.append(
                UserAdminModulePermission(
                    user=user,
                    module_slug=module_slug,
                    access_level=access_level,
                    assigned_by=assigned_by,
                )
            )
            continue
        if existing.access_level != access_level:
            existing.access_level = access_level
            existing.assigned_by = assigned_by
            to_update.append(existing)

    if to_create:
        UserAdminModulePermission.objects.bulk_create(to_create)
    if to_update:
        UserAdminModulePermission.objects.bulk_update(
            to_update,
            fields=["access_level", "assigned_by", "updated_at"],
        )

    if replace:
        keep_modules = set(normalized_permissions.keys())
        UserAdminModulePermission.objects.filter(user=user).exclude(
            module_slug__in=keep_modules
        ).delete()

    if hasattr(user, "_rbac_admin_module_access_map"):
        delattr(user, "_rbac_admin_module_access_map")

    return get_user_admin_module_access_map(user)


def user_can_access_technical_admin(user) -> bool:
    return _has_base_technical_admin_access(user)


def user_has_any_role(user, role_codes: set[str] | list[str] | tuple[str, ...]) -> bool:
    if not user or not getattr(user, "is_authenticated", False):
        return False

    if getattr(user, "is_superuser", False):
        return True

    expected = {code.upper() for code in role_codes}
    if not expected:
        return True

    return not get_user_role_codes(user).isdisjoint(expected)


@transaction.atomic
def register_user_with_default_role(
    *,
    username: str,
    password: str,
    email: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
):
    User = get_user_model()

    if User.objects.filter(username=username).exists():
        raise ValidationError("Nome de usuario ja cadastrado.")

    user = User.objects.create_user(
        username=username,
        email=(email or "").strip(),
        password=password,
        first_name=(first_name or "").strip(),
        last_name=(last_name or "").strip(),
    )

    assign_roles_to_user(user=user, role_codes=[SystemRole.CLIENTE], replace=True)
    return user

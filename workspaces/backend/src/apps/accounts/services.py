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

from .models import Role, UserProfile, UserRole


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

from __future__ import annotations

import hashlib
import secrets
from datetime import timedelta
from urllib.parse import quote, urlparse, urlunparse

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.mail import send_mail
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
EMAIL_VERIFICATION_TOKEN_TTL_HOURS = 24

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
    message = "\n".join(
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
    from_email = (
        str(getattr(settings, "DEFAULT_FROM_EMAIL", "")).strip()
        or "noreply@mrquentinha.local"
    )
    sent_count = send_mail(
        subject=subject,
        message=message,
        from_email=from_email,
        recipient_list=[email_value],
        fail_silently=True,
    )

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

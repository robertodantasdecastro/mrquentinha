from __future__ import annotations

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import Role, UserRole


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

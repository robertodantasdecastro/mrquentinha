from __future__ import annotations

from rest_framework import permissions
from rest_framework.permissions import BasePermission

from .services import SystemRole, user_has_any_role

MANAGEMENT_ROLES = (
    SystemRole.ADMIN,
    SystemRole.FINANCEIRO,
    SystemRole.COZINHA,
    SystemRole.COMPRAS,
    SystemRole.ESTOQUE,
)

CATALOG_READ_ROLES = MANAGEMENT_ROLES
CATALOG_WRITE_ROLES = (SystemRole.ADMIN, SystemRole.COZINHA)
MENU_READ_ROLES = (*MANAGEMENT_ROLES, SystemRole.CLIENTE)
MENU_WRITE_ROLES = (SystemRole.ADMIN, SystemRole.COZINHA)

INVENTORY_READ_ROLES = MANAGEMENT_ROLES
INVENTORY_WRITE_ROLES = (SystemRole.ADMIN, SystemRole.ESTOQUE, SystemRole.COMPRAS)

PROCUREMENT_REQUEST_READ_ROLES = MANAGEMENT_ROLES
PROCUREMENT_REQUEST_WRITE_ROLES = (
    SystemRole.ADMIN,
    SystemRole.COMPRAS,
    SystemRole.COZINHA,
)
PROCUREMENT_FROM_MENU_ROLES = PROCUREMENT_REQUEST_WRITE_ROLES
PROCUREMENT_PURCHASE_READ_ROLES = MANAGEMENT_ROLES
PROCUREMENT_PURCHASE_WRITE_ROLES = (
    SystemRole.ADMIN,
    SystemRole.COMPRAS,
    SystemRole.ESTOQUE,
)

ORDER_CREATE_ROLES = (SystemRole.ADMIN, SystemRole.CLIENTE)
ORDER_READ_ROLES = (*MANAGEMENT_ROLES, SystemRole.CLIENTE)
ORDER_STATUS_UPDATE_ROLES = (
    SystemRole.ADMIN,
    SystemRole.COZINHA,
    SystemRole.FINANCEIRO,
    SystemRole.COMPRAS,
    SystemRole.ESTOQUE,
)
PAYMENT_READ_ROLES = (SystemRole.ADMIN, SystemRole.FINANCEIRO, SystemRole.CLIENTE)
PAYMENT_WRITE_ROLES = (SystemRole.ADMIN, SystemRole.FINANCEIRO)

FINANCE_READ_ROLES = (SystemRole.ADMIN, SystemRole.FINANCEIRO)
FINANCE_WRITE_ROLES = FINANCE_READ_ROLES

PRODUCTION_READ_ROLES = (
    SystemRole.ADMIN,
    SystemRole.COZINHA,
    SystemRole.COMPRAS,
    SystemRole.FINANCEIRO,
)
PRODUCTION_WRITE_ROLES = (SystemRole.ADMIN, SystemRole.COZINHA)

OCR_READ_ROLES = (SystemRole.ADMIN, SystemRole.COZINHA, SystemRole.COMPRAS)
OCR_WRITE_ROLES = OCR_READ_ROLES


class RoleMatrixPermission(BasePermission):
    message = "Voce nao possui permissao para acessar este recurso."

    def has_permission(self, request, view) -> bool:
        user = request.user
        if not user or not user.is_authenticated:
            return False

        if user.is_superuser:
            return True

        required_roles = self._resolve_required_roles(request=request, view=view)
        if required_roles is None:
            return True

        normalized_roles = tuple(code.upper() for code in required_roles if code)
        if not normalized_roles:
            return True

        return user_has_any_role(user, normalized_roles)

    def _resolve_required_roles(self, *, request, view):
        action_map = getattr(view, "required_roles_by_action", None)
        if action_map is not None:
            action = getattr(view, "action", None)
            if action and action in action_map:
                return action_map[action]

            if request.method in permissions.SAFE_METHODS and "read" in action_map:
                return action_map["read"]

            if request.method not in permissions.SAFE_METHODS and "write" in action_map:
                return action_map["write"]

            return action_map.get("*")

        method_map = getattr(view, "required_roles_by_method", None)
        if method_map is not None:
            return method_map.get(request.method.upper()) or method_map.get("*")

        return getattr(view, "required_roles", None)


def is_management_user(user) -> bool:
    if not user or not user.is_authenticated:
        return False

    if user.is_superuser:
        return True

    return user_has_any_role(user, MANAGEMENT_ROLES)

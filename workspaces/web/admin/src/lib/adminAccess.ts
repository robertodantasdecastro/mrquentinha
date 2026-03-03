import type { AuthUserProfile } from "@/types/api";

const TECHNICAL_ADMIN_MODULE_SLUGS = new Set([
  "usuarios-rbac",
  "portal",
  "banco-dados",
  "auditoria-atividade",
  "administracao-servidor",
  "instalacao-deploy",
]);

function hasAdminRole(user: AuthUserProfile | null): boolean {
  if (!user) {
    return false;
  }

  const roleCodes = new Set((user.roles || []).map((role) => role.toUpperCase()));
  return roleCodes.has("ADMIN");
}

export function isTechnicalAdminModule(moduleSlug: string): boolean {
  return TECHNICAL_ADMIN_MODULE_SLUGS.has(moduleSlug);
}

export function canAccessAdminModule(
  user: AuthUserProfile | null,
  moduleSlug: string,
  requiredAccess: "read" | "write" = "read",
): boolean {
  if (!user) {
    return false;
  }

  if (hasAdminRole(user)) {
    return true;
  }

  if (isTechnicalAdminModule(moduleSlug) && !canAccessTechnicalAdmin(user)) {
    return false;
  }

  const permissions = user.module_permissions || [];
  const permission = permissions.find((entry) => entry.module_slug === moduleSlug);
  if (permission) {
    if (requiredAccess === "write") {
      return permission.access_level === "write";
    }
    return true;
  }

  const explicitAllowed = user.allowed_admin_module_slugs || [];
  if (explicitAllowed.length > 0) {
    return explicitAllowed.includes(moduleSlug);
  }

  return false;
}

export function canAccessTechnicalAdmin(user: AuthUserProfile | null): boolean {
  if (!user) {
    return false;
  }

  if (typeof user.can_access_technical_admin === "boolean") {
    return user.can_access_technical_admin;
  }

  return hasAdminRole(user);
}

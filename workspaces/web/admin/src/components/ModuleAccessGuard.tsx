"use client";

import type { ReactNode } from "react";

import { useAdminSession } from "@/components/AdminSessionGate";
import { canAccessAdminModule } from "@/lib/adminAccess";

type ModuleAccessGuardProps = {
  moduleSlug: string;
  moduleLabel: string;
  children: ReactNode;
};

export function ModuleAccessGuard({
  moduleSlug,
  moduleLabel,
  children,
}: ModuleAccessGuardProps) {
  const { user } = useAdminSession();
  const canAccess = canAccessAdminModule(user, moduleSlug);

  if (canAccess) {
    return <>{children}</>;
  }

  return (
    <section className="rounded-2xl border border-amber-300 bg-amber-50 p-6 text-amber-900 shadow-sm">
      <h2 className="text-lg font-semibold">Acesso restrito</h2>
      <p className="mt-2 text-sm">
        O módulo <strong>{moduleLabel}</strong> exige perfil administrativo.
      </p>
      <p className="mt-1 text-sm">
        Solicite a um administrador a atribuição adequada de papel no módulo Usuários e RBAC.
      </p>
    </section>
  );
}

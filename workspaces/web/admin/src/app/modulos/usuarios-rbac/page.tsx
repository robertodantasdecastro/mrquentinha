"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModuleAccessGuard } from "@/components/ModuleAccessGuard";
import { ModulePageShell } from "@/components/ModulePageShell";
import { USUARIOS_RBAC_MENU_ITEMS, UsuariosRbacSections } from "@/app/modulos/usuarios-rbac/sections";

export default function UsuariosRbacModulePage() {
  return (
    <AdminSessionGate>
      <ModuleAccessGuard moduleSlug="usuarios-rbac" moduleLabel="Usuários e RBAC">
        <ModulePageShell
          title="Usuários e RBAC"
          description="Gestão de papéis, permissões e trilha básica de auditoria."
          statusLabel="Baseline ativo"
          statusTone="info"
          menuItems={USUARIOS_RBAC_MENU_ITEMS}
          activeKey="all"
        >
          <UsuariosRbacSections />
        </ModulePageShell>
      </ModuleAccessGuard>
    </AdminSessionGate>
  );
}

"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { USUARIOS_RBAC_MENU_ITEMS, UsuariosRbacSections } from "@/app/modulos/usuarios-rbac/sections";

export default function UsuariosRbacModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Usuarios e RBAC"
        description="Gestao de papeis, permissoes e trilha basica de auditoria."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={USUARIOS_RBAC_MENU_ITEMS}
        activeKey="all"
      >
        <UsuariosRbacSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

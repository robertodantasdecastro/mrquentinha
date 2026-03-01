"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModuleAccessGuard } from "@/components/ModuleAccessGuard";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  SERVER_ADMIN_MENU_ITEMS,
  PortalSections,
} from "@/app/modulos/portal/sections";

export default function AdministracaoServidorModulePage() {
  return (
    <AdminSessionGate>
      <ModuleAccessGuard moduleSlug="administracao-servidor" moduleLabel="Administracao do servidor">
        <ModulePageShell
          title="Administracao do servidor"
          description="Gerencie e-mail, conectividade/dominio e build/release do ecossistema."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={SERVER_ADMIN_MENU_ITEMS}
          activeKey="all"
        >
          <PortalSections mode="server-admin" />
        </ModulePageShell>
      </ModuleAccessGuard>
    </AdminSessionGate>
  );
}

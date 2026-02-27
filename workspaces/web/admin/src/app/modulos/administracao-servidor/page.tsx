"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  SERVER_ADMIN_MENU_ITEMS,
  PortalSections,
} from "@/app/modulos/portal/sections";

export default function AdministracaoServidorModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Administracao do servidor"
        description="Gerencie e-mail, conectividade/dominio, instalacao operacional e build/release."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={SERVER_ADMIN_MENU_ITEMS}
        activeKey="all"
      >
        <PortalSections mode="server-admin" />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

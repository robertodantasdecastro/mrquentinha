"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { PORTAL_MENU_ITEMS, PortalSections } from "@/app/modulos/portal/sections";

export default function PortalModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Portal CMS"
        description="Gerencie templates, autenticacao social, pagamentos, conteudo dinamico e publicacao do Portal e Web Cliente."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={PORTAL_MENU_ITEMS}
        activeKey="all"
      >
        <PortalSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

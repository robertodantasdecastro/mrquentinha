"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { PORTAL_MENU_ITEMS, PortalSections } from "@/app/modulos/portal/sections";

export default function PortalModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Portal CMS"
        description="Gerencie o template ativo do portal e publique a configuracao."
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

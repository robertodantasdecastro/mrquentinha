"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { RELATORIOS_MENU_ITEMS, RelatoriosSections } from "@/app/modulos/relatorios/sections";

export default function RelatoriosModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Relatorios"
        description="Fluxo de caixa global integrado com pedidos, compras e producao."
        statusLabel="Em implementacao"
        statusTone="info"
        menuItems={RELATORIOS_MENU_ITEMS}
        activeKey="all"
      >
        <RelatoriosSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

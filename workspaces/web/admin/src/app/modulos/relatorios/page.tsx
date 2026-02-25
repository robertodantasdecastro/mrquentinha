"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { RELATORIOS_MENU_ITEMS, RelatoriosSections } from "@/app/modulos/relatorios/sections";

export default function RelatoriosModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Relatórios"
        description="Fluxo de caixa global integrado com pedidos, compras e produção."
        statusLabel="Em implementação"
        statusTone="info"
        menuItems={RELATORIOS_MENU_ITEMS}
        activeKey="all"
      >
        <RelatoriosSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

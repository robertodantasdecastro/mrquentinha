"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { PRODUCAO_MENU_ITEMS, ProducaoSections } from "@/app/modulos/producao/sections";

export default function ProducaoModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Produção"
        description="Acompanhe lotes, rendimento e comparativo planejado x produzido."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={PRODUCAO_MENU_ITEMS}
        activeKey="all"
      >
        <ProducaoSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

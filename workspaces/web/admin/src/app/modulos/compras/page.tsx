"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { COMPRAS_MENU_ITEMS, ComprasSections } from "@/app/modulos/compras/sections";

export default function ComprasModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Compras"
        description="Requisicoes, compras confirmadas e impacto no fluxo de caixa."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={COMPRAS_MENU_ITEMS}
        activeKey="all"
      >
        <ComprasSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

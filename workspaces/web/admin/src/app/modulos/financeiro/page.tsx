"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { FINANCEIRO_MENU_ITEMS, FinanceiroSections } from "@/app/modulos/financeiro/sections";

export default function FinanceiroModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Financeiro"
        description="Fluxo de caixa global, conciliação e indicadores financeiros integrados."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={FINANCEIRO_MENU_ITEMS}
        activeKey="all"
      >
        <FinanceiroSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

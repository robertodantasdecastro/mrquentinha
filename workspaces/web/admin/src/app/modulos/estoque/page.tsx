"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { ESTOQUE_MENU_ITEMS, EstoqueSections } from "@/app/modulos/estoque/sections";

export default function EstoqueModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Estoque"
        description="Controle de saldo, alertas de reposicao e rastreio de movimentos."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={ESTOQUE_MENU_ITEMS}
        activeKey="all"
      >
        <EstoqueSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

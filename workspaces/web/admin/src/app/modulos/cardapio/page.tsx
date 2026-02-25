"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { CARDAPIO_MENU_ITEMS, CardapioSections } from "@/app/modulos/cardapio/sections";

export default function CardapioModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Cardapio"
        description="Planejamento de menus, pratos e volume esperado por dia."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={CARDAPIO_MENU_ITEMS}
        activeKey="all"
      >
        <CardapioSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

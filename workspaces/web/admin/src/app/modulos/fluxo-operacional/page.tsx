"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  FLUXO_MENU_ITEMS,
  FluxoOperacionalSections,
} from "@/app/modulos/fluxo-operacional/sections";

export default function FluxoOperacionalPage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Fluxo operacional guiado"
        description="Modo passo a passo para conduzir receitas/cardapio, compras, producao, pedidos, financeiro e relatorios."
        statusLabel="Guia ativo"
        statusTone="info"
        menuItems={FLUXO_MENU_ITEMS}
        activeKey="all"
      >
        <FluxoOperacionalSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

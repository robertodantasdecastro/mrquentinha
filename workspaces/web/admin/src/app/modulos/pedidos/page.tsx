"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { PEDIDOS_MENU_ITEMS, PedidosSections } from "@/app/modulos/pedidos/sections";

export default function PedidosModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Pedidos"
        description="Acompanhe a fila do dia, status por etapa e conversao de pagamentos."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={PEDIDOS_MENU_ITEMS}
        activeKey="all"
      >
        <PedidosSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

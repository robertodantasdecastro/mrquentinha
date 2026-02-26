"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  MONITORAMENTO_MENU_ITEMS,
  MonitoramentoSections,
} from "@/app/modulos/monitoramento/sections";

export default function MonitoramentoModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Monitoramento"
        description="Visao realtime de servicos, pagamentos e lifecycle do pedido."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={MONITORAMENTO_MENU_ITEMS}
        activeKey="all"
      >
        <MonitoramentoSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

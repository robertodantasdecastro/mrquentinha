"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  MONITORAMENTO_MENU_ITEMS,
  MonitoramentoSections,
  type MonitoramentoSectionKey,
} from "@/app/modulos/monitoramento/sections";

const SECTION_KEYS: MonitoramentoSectionKey[] = [
  "all",
  "visao-geral",
  "servicos",
  "pagamentos",
  "lifecycle",
];

function resolveSectionKey(
  value: string | string[] | undefined,
): MonitoramentoSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as MonitoramentoSectionKey)
      ? (value[0] as MonitoramentoSectionKey)
      : "all";
  }

  return SECTION_KEYS.includes(value as MonitoramentoSectionKey)
    ? (value as MonitoramentoSectionKey)
    : "all";
}

export default function MonitoramentoServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Monitoramento"
        description="Visao realtime de servicos, pagamentos e lifecycle do pedido."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={MONITORAMENTO_MENU_ITEMS}
        activeKey={service}
      >
        <MonitoramentoSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

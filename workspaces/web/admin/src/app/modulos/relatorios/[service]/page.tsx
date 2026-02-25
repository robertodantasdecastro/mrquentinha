"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  RELATORIOS_MENU_ITEMS,
  RelatoriosSections,
  type RelatoriosSectionKey,
} from "@/app/modulos/relatorios/sections";

const SECTION_KEYS: RelatoriosSectionKey[] = [
  "all",
  "fluxo-caixa",
  "compras",
  "producao",
  "pedidos",
  "exportacao",
];

function resolveSectionKey(value: string | string[] | undefined): RelatoriosSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as RelatoriosSectionKey) ? (value[0] as RelatoriosSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as RelatoriosSectionKey) ? (value as RelatoriosSectionKey) : "all";
}

export default function RelatoriosServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Relatórios"
        description="Fluxo de caixa global integrado com pedidos, compras e produção."
        statusLabel="Em implementação"
        statusTone="info"
        menuItems={RELATORIOS_MENU_ITEMS}
        activeKey={service}
      >
        <RelatoriosSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

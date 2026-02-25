"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  FINANCEIRO_MENU_ITEMS,
  FinanceiroSections,
  type FinanceiroSectionKey,
} from "@/app/modulos/financeiro/sections";

const SECTION_KEYS: FinanceiroSectionKey[] = [
  "all",
  "visao-geral",
  "conciliacao",
  "tendencias",
  "exportacao",
];

function resolveSectionKey(value: string | string[] | undefined): FinanceiroSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as FinanceiroSectionKey)
      ? (value[0] as FinanceiroSectionKey)
      : "all";
  }

  return SECTION_KEYS.includes(value as FinanceiroSectionKey)
    ? (value as FinanceiroSectionKey)
    : "all";
}

export default function FinanceiroServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Financeiro"
        description="Fluxo de caixa global, conciliação e indicadores financeiros integrados."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={FINANCEIRO_MENU_ITEMS}
        activeKey={service}
      >
        <FinanceiroSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

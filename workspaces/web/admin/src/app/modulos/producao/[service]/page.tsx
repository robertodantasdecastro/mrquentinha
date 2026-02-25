"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  PRODUCAO_MENU_ITEMS,
  ProducaoSections,
  type ProducaoSectionKey,
} from "@/app/modulos/producao/sections";

const SECTION_KEYS: ProducaoSectionKey[] = ["all", "visao-geral", "lotes", "tendencias", "exportacao"];

function resolveSectionKey(value: string | string[] | undefined): ProducaoSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as ProducaoSectionKey) ? (value[0] as ProducaoSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as ProducaoSectionKey) ? (value as ProducaoSectionKey) : "all";
}

export default function ProducaoServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Produção"
        description="Acompanhe lotes, rendimento e comparativo planejado x produzido."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={PRODUCAO_MENU_ITEMS}
        activeKey={service}
      >
        <ProducaoSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

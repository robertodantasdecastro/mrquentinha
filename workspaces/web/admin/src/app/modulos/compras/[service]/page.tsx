"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  COMPRAS_MENU_ITEMS,
  ComprasSections,
  type ComprasSectionKey,
} from "@/app/modulos/compras/sections";

const SECTION_KEYS: ComprasSectionKey[] = ["all", "visao-geral", "operacao", "impacto", "exportacao"];

function resolveSectionKey(value: string | string[] | undefined): ComprasSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as ComprasSectionKey) ? (value[0] as ComprasSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as ComprasSectionKey) ? (value as ComprasSectionKey) : "all";
}

export default function ComprasServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Compras"
        description="Requisicoes, compras confirmadas e impacto no fluxo de caixa."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={COMPRAS_MENU_ITEMS}
        activeKey={service}
      >
        <ComprasSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

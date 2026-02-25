"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  ESTOQUE_MENU_ITEMS,
  EstoqueSections,
  type EstoqueSectionKey,
} from "@/app/modulos/estoque/sections";

const SECTION_KEYS: EstoqueSectionKey[] = ["all", "visao-geral", "movimentos", "tendencias"];

function resolveSectionKey(value: string | string[] | undefined): EstoqueSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as EstoqueSectionKey) ? (value[0] as EstoqueSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as EstoqueSectionKey) ? (value as EstoqueSectionKey) : "all";
}

export default function EstoqueServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Estoque"
        description="Controle de saldo, alertas de reposicao e rastreio de movimentos."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={ESTOQUE_MENU_ITEMS}
        activeKey={service}
      >
        <EstoqueSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

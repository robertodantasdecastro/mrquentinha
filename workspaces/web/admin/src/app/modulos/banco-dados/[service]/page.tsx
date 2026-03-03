"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModuleAccessGuard } from "@/components/ModuleAccessGuard";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  BANCO_DADOS_MENU_ITEMS,
  BancoDadosSections,
  type BancoDadosSectionKey,
} from "@/app/modulos/banco-dados/sections";

const SECTION_KEYS: BancoDadosSectionKey[] = ["all", "guia", "ssh", "backup", "sync-dev"];

function resolveSectionKey(value: string | string[] | undefined): BancoDadosSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as BancoDadosSectionKey)
      ? (value[0] as BancoDadosSectionKey)
      : "all";
  }
  return SECTION_KEYS.includes(value as BancoDadosSectionKey)
    ? (value as BancoDadosSectionKey)
    : "all";
}

export default function BancoDadosServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModuleAccessGuard moduleSlug="banco-dados" moduleLabel="Banco de dados">
        <ModulePageShell
          title="Banco de dados"
          description="Backups, restore remoto e sincronizacao de dados entre producao e DEV."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={BANCO_DADOS_MENU_ITEMS}
          activeKey={service}
        >
          <BancoDadosSections activeSection={service} />
        </ModulePageShell>
      </ModuleAccessGuard>
    </AdminSessionGate>
  );
}

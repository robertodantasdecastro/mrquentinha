"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  CLIENTES_MENU_ITEMS,
  ClientesSections,
  type ClientesSectionKey,
} from "@/app/modulos/clientes/sections";

const SECTION_KEYS: ClientesSectionKey[] = ["all", "gestao", "compliance", "operacao"];

function resolveSectionKey(value: string | string[] | undefined): ClientesSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as ClientesSectionKey) ? (value[0] as ClientesSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as ClientesSectionKey) ? (value as ClientesSectionKey) : "all";
}

export default function ClientesServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Clientes"
        description="Gestao completa de clientes para ecommerce, com KYC, compliance LGPD e governanca de checkout."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={CLIENTES_MENU_ITEMS}
        activeKey={service}
      >
        <ClientesSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

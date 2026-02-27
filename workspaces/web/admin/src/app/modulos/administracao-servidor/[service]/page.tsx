"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  SERVER_ADMIN_MENU_ITEMS,
  PortalSections,
  type ServerAdminSectionKey,
} from "@/app/modulos/portal/sections";

const SECTION_KEYS: ServerAdminSectionKey[] = [
  "all",
  "email",
  "conectividade",
  "mobile-build",
];

function resolveSectionKey(value: string | string[] | undefined): ServerAdminSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as ServerAdminSectionKey) ? (value[0] as ServerAdminSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as ServerAdminSectionKey) ? (value as ServerAdminSectionKey) : "all";
}

export default function AdministracaoServidorServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Administracao do servidor"
        description="Gerencie e-mail, conectividade/dominio, instalacao operacional e build/release."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={SERVER_ADMIN_MENU_ITEMS}
        activeKey={service}
      >
        <PortalSections mode="server-admin" activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

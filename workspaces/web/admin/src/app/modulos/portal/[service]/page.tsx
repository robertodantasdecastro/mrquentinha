"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  PORTAL_MENU_ITEMS,
  PortalSections,
  type PortalSectionKey,
} from "@/app/modulos/portal/sections";

const SECTION_KEYS: PortalSectionKey[] = ["all", "template", "publicacao"];

function resolveSectionKey(value: string | string[] | undefined): PortalSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as PortalSectionKey) ? (value[0] as PortalSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as PortalSectionKey) ? (value as PortalSectionKey) : "all";
}

export default function PortalServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Portal CMS"
        description="Gerencie o template ativo do portal e publique a configuracao."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={PORTAL_MENU_ITEMS}
        activeKey={service}
      >
        <PortalSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

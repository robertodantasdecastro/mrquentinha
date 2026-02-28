"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  INSTALL_DEPLOY_MENU_ITEMS,
  InstallDeploySections,
  type InstallDeploySectionKey,
} from "@/app/modulos/instalacao-deploy/sections";

const SECTION_KEYS: InstallDeploySectionKey[] = ["all", "pre-requisitos", "assistente"];

function resolveSectionKey(value: string | string[] | undefined): InstallDeploySectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as InstallDeploySectionKey)
      ? (value[0] as InstallDeploySectionKey)
      : "all";
  }

  return SECTION_KEYS.includes(value as InstallDeploySectionKey)
    ? (value as InstallDeploySectionKey)
    : "all";
}

export default function InstalacaoDeployServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Instalacao / Deploy"
        description="Assistente guiado para instalacao local/remota e deploy com DNS, dominios e pre-requisitos de producao."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={INSTALL_DEPLOY_MENU_ITEMS}
        activeKey={service}
      >
        <InstallDeploySections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

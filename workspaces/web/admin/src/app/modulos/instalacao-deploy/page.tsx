"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  INSTALL_DEPLOY_MENU_ITEMS,
  InstallDeploySections,
} from "@/app/modulos/instalacao-deploy/sections";

export default function InstalacaoDeployModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Instalacao / Deploy"
        description="Assistente guiado para instalacao local/remota e deploy com DNS, dominios e pre-requisitos de producao."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={INSTALL_DEPLOY_MENU_ITEMS}
        activeKey="all"
      >
        <InstallDeploySections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModuleAccessGuard } from "@/components/ModuleAccessGuard";
import { ModulePageShell } from "@/components/ModulePageShell";
import { BANCO_DADOS_MENU_ITEMS, BancoDadosSections } from "@/app/modulos/banco-dados/sections";

export default function BancoDadosModulePage() {
  return (
    <AdminSessionGate>
      <ModuleAccessGuard moduleSlug="banco-dados" moduleLabel="Banco de dados">
        <ModulePageShell
          title="Banco de dados"
          description="Backups, restore remoto e sincronizacao de dados entre producao e DEV."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={BANCO_DADOS_MENU_ITEMS}
          activeKey="all"
        >
          <BancoDadosSections />
        </ModulePageShell>
      </ModuleAccessGuard>
    </AdminSessionGate>
  );
}

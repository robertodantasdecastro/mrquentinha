"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { CLIENTES_MENU_ITEMS, ClientesSections } from "@/app/modulos/clientes/sections";

export default function ClientesModulePage() {
  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Clientes"
        description="Gestao completa de clientes para ecommerce, com KYC, compliance LGPD e governanca de checkout."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={CLIENTES_MENU_ITEMS}
        activeKey="all"
      >
        <ClientesSections />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

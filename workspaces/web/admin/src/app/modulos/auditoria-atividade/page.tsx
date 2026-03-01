"use client";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModuleAccessGuard } from "@/components/ModuleAccessGuard";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  AUDITORIA_ATIVIDADE_MENU_ITEMS,
  AuditoriaAtividadeSections,
} from "@/app/modulos/auditoria-atividade/sections";

export default function AuditoriaAtividadeModulePage() {
  return (
    <AdminSessionGate>
      <ModuleAccessGuard
        moduleSlug="auditoria-atividade"
        moduleLabel="Auditoria de atividade"
      >
        <ModulePageShell
          title="Auditoria de atividade"
          description="Governanca operacional do Web Admin com trilha de eventos, indicadores, risco e investigacao detalhada."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={AUDITORIA_ATIVIDADE_MENU_ITEMS}
          activeKey="all"
        >
          <AuditoriaAtividadeSections />
        </ModulePageShell>
      </ModuleAccessGuard>
    </AdminSessionGate>
  );
}

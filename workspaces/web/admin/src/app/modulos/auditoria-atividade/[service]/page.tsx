"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModuleAccessGuard } from "@/components/ModuleAccessGuard";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  AUDITORIA_ATIVIDADE_MENU_ITEMS,
  AuditoriaAtividadeSections,
  type AuditoriaAtividadeSectionKey,
} from "@/app/modulos/auditoria-atividade/sections";

const SECTION_KEYS: AuditoriaAtividadeSectionKey[] = [
  "all",
  "visao-geral",
  "eventos",
  "seguranca",
  "tendencias",
];

function resolveSectionKey(
  value: string | string[] | undefined,
): AuditoriaAtividadeSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as AuditoriaAtividadeSectionKey)
      ? (value[0] as AuditoriaAtividadeSectionKey)
      : "all";
  }

  return SECTION_KEYS.includes(value as AuditoriaAtividadeSectionKey)
    ? (value as AuditoriaAtividadeSectionKey)
    : "all";
}

export default function AuditoriaAtividadeServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

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
          activeKey={service}
        >
          <AuditoriaAtividadeSections activeSection={service} />
        </ModulePageShell>
      </ModuleAccessGuard>
    </AdminSessionGate>
  );
}

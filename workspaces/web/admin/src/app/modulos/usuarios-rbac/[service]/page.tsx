"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  USUARIOS_RBAC_MENU_ITEMS,
  UsuariosRbacSections,
  type UsuariosRbacSectionKey,
} from "@/app/modulos/usuarios-rbac/sections";

const SECTION_KEYS: UsuariosRbacSectionKey[] = ["all", "visao-geral", "usuarios", "tendencias"];

function resolveSectionKey(value: string | string[] | undefined): UsuariosRbacSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as UsuariosRbacSectionKey) ? (value[0] as UsuariosRbacSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as UsuariosRbacSectionKey) ? (value as UsuariosRbacSectionKey) : "all";
}

export default function UsuariosRbacServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Usuários e RBAC"
        description="Gestão de papéis, permissões e trilha básica de auditoria."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={USUARIOS_RBAC_MENU_ITEMS}
        activeKey={service}
      >
        <UsuariosRbacSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

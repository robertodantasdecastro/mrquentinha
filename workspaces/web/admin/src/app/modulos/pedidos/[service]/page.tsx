"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  PEDIDOS_MENU_ITEMS,
  PedidosSections,
  type PedidosSectionKey,
} from "@/app/modulos/pedidos/sections";

const SECTION_KEYS: PedidosSectionKey[] = [
  "all",
  "visao-geral",
  "operacao",
  "tendencias",
  "exportacao",
];

function resolveSectionKey(value: string | string[] | undefined): PedidosSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as PedidosSectionKey)
      ? (value[0] as PedidosSectionKey)
      : "all";
  }

  return SECTION_KEYS.includes(value as PedidosSectionKey)
    ? (value as PedidosSectionKey)
    : "all";
}

export default function PedidosServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Pedidos"
        description="Acompanhe a fila do dia, status por etapa e conversao de pagamentos."
        statusLabel="Ativo"
        statusTone="success"
        menuItems={PEDIDOS_MENU_ITEMS}
        activeKey={service}
      >
        <PedidosSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

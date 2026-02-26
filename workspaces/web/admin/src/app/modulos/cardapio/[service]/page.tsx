"use client";

import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  CARDAPIO_MENU_ITEMS,
  CardapioSections,
  type CardapioSectionKey,
} from "@/app/modulos/cardapio/sections";

const SECTION_KEYS: CardapioSectionKey[] = ["all", "planejamento", "composicao", "menus", "tendencias"];

function resolveSectionKey(value: string | string[] | undefined): CardapioSectionKey {
  if (Array.isArray(value)) {
    return SECTION_KEYS.includes(value[0] as CardapioSectionKey) ? (value[0] as CardapioSectionKey) : "all";
  }

  return SECTION_KEYS.includes(value as CardapioSectionKey) ? (value as CardapioSectionKey) : "all";
}

export default function CardapioServicePage() {
  const params = useParams();
  const service = resolveSectionKey(params?.service);

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Cardapio"
        description="Planejamento de menus, pratos e volume esperado por dia."
        statusLabel="Baseline ativo"
        statusTone="info"
        menuItems={CARDAPIO_MENU_ITEMS}
        activeKey={service}
      >
        <CardapioSections activeSection={service} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

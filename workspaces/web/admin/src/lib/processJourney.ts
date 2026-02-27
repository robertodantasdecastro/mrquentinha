export type ProcessJourneyStep = {
  slug: string;
  title: string;
  description: string;
  moduleHref: string;
  moduleLabel: string;
};

export const PROCESS_JOURNEY_STEPS: ProcessJourneyStep[] = [
  {
    slug: "cardapio",
    title: "1. Receitas e cardapio",
    description:
      "Defina pratos, rendimento e menu do dia para gerar demanda operacional.",
    moduleHref: "/modulos/cardapio",
    moduleLabel: "Abrir cardapio",
  },
  {
    slug: "compras",
    title: "2. Compras",
    description:
      "Consolide requisicoes de insumos, OCR de notas e entrada de abastecimento.",
    moduleHref: "/modulos/compras",
    moduleLabel: "Abrir compras",
  },
  {
    slug: "producao",
    title: "3. Producao",
    description:
      "Execute lotes planejados, acompanhe rendimento e finalize producao.",
    moduleHref: "/modulos/producao",
    moduleLabel: "Abrir producao",
  },
  {
    slug: "pedidos",
    title: "4. Pedidos",
    description:
      "Monitore fila, atualize status em tempo real e mantenha SLA de entrega.",
    moduleHref: "/modulos/pedidos",
    moduleLabel: "Abrir pedidos",
  },
  {
    slug: "financeiro",
    title: "5. Financeiro",
    description:
      "Concilie pagamentos, valide caixa e ajuste pendencias de recebimento.",
    moduleHref: "/modulos/financeiro",
    moduleLabel: "Abrir financeiro",
  },
  {
    slug: "relatorios",
    title: "6. Relatorios",
    description:
      "Feche o ciclo com visao detalhada de compras, producao, pedidos e caixa.",
    moduleHref: "/modulos/relatorios",
    moduleLabel: "Abrir relatorios",
  },
];

export function getJourneyStepIndex(stepSlug: string): number {
  return PROCESS_JOURNEY_STEPS.findIndex((step) => step.slug === stepSlug);
}

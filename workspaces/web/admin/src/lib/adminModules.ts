export type AdminModule = {
  slug: string;
  title: string;
  description: string;
  stage: string;
  status: string;
  path: string;
};

export const ADMIN_MODULES: AdminModule[] = [
  {
    slug: "pedidos",
    title: "Pedidos",
    description: "Fila do dia, mudança de status e atendimento operacional.",
    stage: "T9.0.2",
    status: "ativo",
    path: "/modulos/pedidos",
  },
  {
    slug: "financeiro",
    title: "Financeiro",
    description: "KPIs, caixa não conciliado e visão de risco diário.",
    stage: "T9.0.2",
    status: "ativo",
    path: "/modulos/financeiro",
  },
  {
    slug: "estoque",
    title: "Estoque",
    description: "Saldo por ingrediente, alertas e registro de movimentos.",
    stage: "T9.0.2",
    status: "ativo",
    path: "/modulos/estoque",
  },
  {
    slug: "cardapio",
    title: "Cardápio",
    description: "Menus e pratos com baseline de planejamento operacional.",
    stage: "T9.1.1",
    status: "ativo (baseline)",
    path: "/modulos/cardapio",
  },
  {
    slug: "compras",
    title: "Compras",
    description: "Requisições e compras recentes com visão de abastecimento.",
    stage: "T9.1.1",
    status: "ativo (baseline)",
    path: "/modulos/compras",
  },
  {
    slug: "producao",
    title: "Produção",
    description: "Lotes por data com acompanhamento de planejado x produzido.",
    stage: "T9.1.1",
    status: "ativo (baseline)",
    path: "/modulos/producao",
  },
  {
    slug: "usuarios-rbac",
    title: "Usuários/RBAC",
    description: "Gestão de papéis, permissões e trilha de auditoria básica.",
    stage: "T9.1.1",
    status: "ativo (baseline)",
    path: "/modulos/usuarios-rbac",
  },
  {
    slug: "relatorios",
    title: "Relatórios",
    description: "Fluxo de caixa global, compras, produção e exportações em CSV.",
    stage: "T9.1.2",
    status: "ativo",
    path: "/modulos/relatorios",
  },
  {
    slug: "portal",
    title: "Portal CMS",
    description: "Templates, conectividade e publicacao do Portal e Web Cliente.",
    stage: "T6.3.2",
    status: "ativo",
    path: "/modulos/portal",
  },
];

export function resolveModuleStatusTone(status: string):
  | "success"
  | "warning"
  | "danger"
  | "info"
  | "neutral" {
  const normalizedStatus = status.toLowerCase();

  if (normalizedStatus.includes("planejado")) {
    return "warning";
  }

  if (normalizedStatus.includes("baseline")) {
    return "info";
  }

  if (normalizedStatus.includes("ativo")) {
    return "success";
  }

  if (normalizedStatus.includes("implementacao") || normalizedStatus.includes("implementação")) {
    return "info";
  }

  return "neutral";
}

export function resolveModuleCardBorder(status: string): string {
  const tone = resolveModuleStatusTone(status);

  if (tone === "success") {
    return "border-status-success/35";
  }

  if (tone === "info") {
    return "border-status-info/35";
  }

  if (tone === "warning") {
    return "border-status-warning/35";
  }

  if (tone === "danger") {
    return "border-status-danger/35";
  }

  return "border-border";
}

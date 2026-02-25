<<<<<<< Updated upstream
=======
"use client";

>>>>>>> Stashed changes
import { StatusPill } from "@mrquentinha/ui";
import { useSearchParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { FinanceOpsPanel } from "@/components/modules/FinanceOpsPanel";

const BASE_PATH = "/modulos/financeiro";

const MENU_ITEMS = [
  { key: "all", label: "Todos", href: BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${BASE_PATH}?view=visao-geral#visao-geral` },
  { key: "conciliacao", label: "Conciliacao", href: `${BASE_PATH}?view=conciliacao#conciliacao` },
  { key: "tendencias", label: "Tendencias", href: `${BASE_PATH}?view=tendencias#tendencias` },
  { key: "exportacao", label: "Exportacao", href: `${BASE_PATH}?view=exportacao#exportacao` },
];

export default function FinanceiroModulePage() {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "all";
  const showAll = activeView === "all";

  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Financeiro"
          description="Fluxo de caixa global, conciliacao e indicadores financeiros integrados."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={MENU_ITEMS}
          activeKey={activeView}
        >
          {(showAll || activeView === "visao-geral") && (
            <section id="visao-geral" className="scroll-mt-24">
              <FinanceOpsPanel />
            </section>
          )}

          {(showAll || activeView === "conciliacao") && (
            <section id="conciliacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Conciliacao global</h2>
                  <p className="mt-1 text-sm text-muted">
                    Movimentos pendentes e origem financeira por modulo.
                  </p>
                </div>
                <StatusPill tone="warning">Pendencias 6</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos</p>
                  <p className="mt-1 text-xl font-semibold text-text">R$ 3.480</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras</p>
                  <p className="mt-1 text-xl font-semibold text-text">R$ 1.220</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Producao</p>
                  <p className="mt-1 text-xl font-semibold text-text">R$ 860</p>
                </article>
              </div>
            </section>
          )}

          {(showAll || activeView === "tendencias") && (
            <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Tendencias financeiras</h2>
                  <p className="mt-1 text-sm text-muted">
                    Receita, despesas e margem por periodo.
                  </p>
                </div>
                <StatusPill tone="brand">Margem 22%</StatusPill>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Fluxo de caixa</p>
                  <Sparkline values={[18, 22, 15, 28, 34, 26, 40]} className="mt-3" />
                </div>
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Despesas por categoria</p>
                  <div className="mt-4">
                    <MiniBarChart values={[12, 18, 9, 22, 14]} />
                  </div>
                </div>
              </div>
            </section>
          )}

          {(showAll || activeView === "exportacao") && (
            <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-text">Exportacao CSV</h2>
              <p className="mt-1 text-sm text-muted">
                Exporte fluxos consolidados e demonstrativos por periodo.
              </p>
              <button
                type="button"
                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
              >
                Exportar financeiro (CSV)
              </button>
            </section>
          )}
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

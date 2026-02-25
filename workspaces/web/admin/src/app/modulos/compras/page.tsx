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
import { ProcurementOpsPanel } from "@/components/modules/ProcurementOpsPanel";

const BASE_PATH = "/modulos/compras";

const MENU_ITEMS = [
  { key: "all", label: "Todos", href: BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${BASE_PATH}?view=visao-geral#visao-geral` },
  { key: "operacao", label: "Operacao", href: `${BASE_PATH}?view=operacao#operacao` },
  { key: "impacto", label: "Impacto", href: `${BASE_PATH}?view=impacto#impacto` },
  { key: "exportacao", label: "Exportacao", href: `${BASE_PATH}?view=exportacao#exportacao` },
];

export default function ComprasModulePage() {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "all";
  const showAll = activeView === "all";

  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Compras"
          description="Requisicoes, compras confirmadas e impacto no fluxo de caixa."
          statusLabel="Baseline ativo"
          statusTone="info"
          menuItems={MENU_ITEMS}
          activeKey={activeView}
        >
          {(showAll || activeView === "visao-geral") && (
            <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Visao geral</h2>
                  <p className="mt-1 text-sm text-muted">Acompanhe requisicoes abertas e compras do periodo.</p>
                </div>
                <StatusPill tone="warning">Pendencias 4</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Requisicoes abertas</p>
                  <p className="mt-1 text-2xl font-semibold text-text">5</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras aprovadas</p>
                  <p className="mt-1 text-2xl font-semibold text-text">3</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Impacto estimado</p>
                  <p className="mt-1 text-2xl font-semibold text-text">R$ 1.620</p>
                </article>
              </div>
            </section>
          )}

          {(showAll || activeView === "operacao") && (
            <section id="operacao" className="scroll-mt-24">
              <ProcurementOpsPanel />
            </section>
          )}

          {(showAll || activeView === "impacto") && (
            <section id="impacto" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Impacto financeiro</h2>
                  <p className="mt-1 text-sm text-muted">Comparativo de fornecedores e itens criticos.</p>
                </div>
                <StatusPill tone="info">Variacao 6%</StatusPill>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras por semana</p>
                  <Sparkline values={[14, 18, 12, 22, 16, 24, 19]} className="mt-3" />
                </div>
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top fornecedores</p>
                  <div className="mt-4">
                    <MiniBarChart values={[10, 14, 8, 12, 9]} />
                  </div>
                </div>
              </div>
            </section>
          )}

          {(showAll || activeView === "exportacao") && (
            <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-text">Exportacao CSV</h2>
              <p className="mt-1 text-sm text-muted">Gere relatorios de compras consolidados por periodo.</p>
              <button
                type="button"
                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
              >
                Exportar compras (CSV)
              </button>
            </section>
          )}
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

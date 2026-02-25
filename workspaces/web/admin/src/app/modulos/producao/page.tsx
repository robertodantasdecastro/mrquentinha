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
import { ProductionOpsPanel } from "@/components/modules/ProductionOpsPanel";

const BASE_PATH = "/modulos/producao";

const MENU_ITEMS = [
  { key: "all", label: "Todos", href: BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${BASE_PATH}?view=visao-geral#visao-geral` },
  { key: "lotes", label: "Lotes", href: `${BASE_PATH}?view=lotes#lotes` },
  { key: "tendencias", label: "Tendencias", href: `${BASE_PATH}?view=tendencias#tendencias` },
  { key: "exportacao", label: "Exportacao", href: `${BASE_PATH}?view=exportacao#exportacao` },
];

export default function ProducaoModulePage() {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "all";
  const showAll = activeView === "all";

  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Producao"
          description="Acompanhe lotes, rendimento e comparativo planejado x produzido."
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
                  <p className="mt-1 text-sm text-muted">Controle de lotes e alertas de divergencia.</p>
                </div>
                <StatusPill tone="warning">2 divergencias</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Lotes do dia</p>
                  <p className="mt-1 text-2xl font-semibold text-text">4</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Planejado</p>
                  <p className="mt-1 text-2xl font-semibold text-text">120</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Produzido</p>
                  <p className="mt-1 text-2xl font-semibold text-text">112</p>
                </article>
              </div>
            </section>
          )}

          {(showAll || activeView === "lotes") && (
            <section id="lotes" className="scroll-mt-24">
              <ProductionOpsPanel />
            </section>
          )}

          {(showAll || activeView === "tendencias") && (
            <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Tendencias de producao</h2>
                  <p className="mt-1 text-sm text-muted">Comparativo planejado x produzido por semana.</p>
                </div>
                <StatusPill tone="info">Rendimento 93%</StatusPill>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Planejado x produzido</p>
                  <Sparkline values={[20, 24, 22, 26, 28, 25, 30]} className="mt-3" />
                </div>
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Perdas por lote</p>
                  <div className="mt-4">
                    <MiniBarChart values={[4, 6, 3, 5, 4]} />
                  </div>
                </div>
              </div>
            </section>
          )}

          {(showAll || activeView === "exportacao") && (
            <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-text">Exportacao CSV</h2>
              <p className="mt-1 text-sm text-muted">Relatorios de producao para comparativo operacional.</p>
              <button
                type="button"
                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
              >
                Exportar producao (CSV)
              </button>
            </section>
          )}
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

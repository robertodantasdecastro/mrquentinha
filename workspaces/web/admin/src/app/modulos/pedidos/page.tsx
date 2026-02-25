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
import { OrdersOpsPanel } from "@/components/modules/OrdersOpsPanel";

const BASE_PATH = "/modulos/pedidos";

const MENU_ITEMS = [
  { key: "all", label: "Todos", href: BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${BASE_PATH}?view=visao-geral#visao-geral` },
  { key: "operacao", label: "Operacao", href: `${BASE_PATH}?view=operacao#operacao` },
  { key: "tendencias", label: "Tendencias", href: `${BASE_PATH}?view=tendencias#tendencias` },
  { key: "exportacao", label: "Exportacao", href: `${BASE_PATH}?view=exportacao#exportacao` },
];

export default function PedidosModulePage() {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "all";
  const showAll = activeView === "all";

  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Pedidos"
          description="Acompanhe a fila do dia, status por etapa e conversao de pagamentos."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={MENU_ITEMS}
          activeKey={activeView}
        >
          {(showAll || activeView === "visao-geral") && (
            <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Visao geral</h2>
                  <p className="mt-1 text-sm text-muted">
                    Fluxo operacional do dia com foco em conversao e atendimento.
                  </p>
                </div>
                <StatusPill tone="info">Hoje</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos ativos</p>
                  <p className="mt-1 text-2xl font-semibold text-text">42</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Em preparo</p>
                  <p className="mt-1 text-2xl font-semibold text-text">18</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Entregues</p>
                  <p className="mt-1 text-2xl font-semibold text-text">21</p>
                </article>
              </div>
            </section>
          )}

          {(showAll || activeView === "operacao") && (
            <section id="operacao" className="scroll-mt-24">
              <OrdersOpsPanel />
            </section>
          )}

          {(showAll || activeView === "tendencias") && (
            <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Tendencias de pedidos</h2>
                  <p className="mt-1 text-sm text-muted">Volume por hora e conversao nos ultimos dias.</p>
                </div>
                <StatusPill tone="brand">Conversao 78%</StatusPill>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pico horario</p>
                  <Sparkline values={[12, 18, 26, 22, 30, 28, 34, 26]} className="mt-3" />
                </div>
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos por canal</p>
                  <div className="mt-4">
                    <MiniBarChart values={[18, 26, 12, 30, 22]} />
                  </div>
                </div>
              </div>
            </section>
          )}

          {(showAll || activeView === "exportacao") && (
            <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <h2 className="text-lg font-semibold text-text">Exportacao CSV</h2>
              <p className="mt-1 text-sm text-muted">
                Gere arquivos CSV com filtros aplicados para reconciliacao financeira.
              </p>
              <button
                type="button"
                className="mt-4 rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
              >
                Exportar pedidos (CSV)
              </button>
            </section>
          )}
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

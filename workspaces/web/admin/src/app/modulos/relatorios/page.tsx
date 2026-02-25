import { StatusPill } from "@mrquentinha/ui";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";

const MENU_ITEMS = [
  { label: "Fluxo de caixa", href: "#fluxo-caixa" },
  { label: "Compras", href: "#compras" },
  { label: "Producao", href: "#producao" },
  { label: "Pedidos", href: "#pedidos" },
  { label: "Exportacao", href: "#exportacao" },
];

export default function RelatoriosModulePage() {
  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Relatorios"
          description="Fluxo de caixa global integrado com pedidos, compras e producao."
          statusLabel="Em implementacao"
          statusTone="info"
          menuItems={MENU_ITEMS}
        >
          <section id="fluxo-caixa" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-text">Fluxo de caixa global</h2>
                <p className="mt-1 text-sm text-muted">Entradas, saidas e saldo consolidado.</p>
              </div>
              <StatusPill tone="brand">Saldo positivo</StatusPill>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Saldo por periodo</p>
                <Sparkline values={[24, 26, 22, 28, 31, 30, 35]} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Entradas vs saidas</p>
                <div className="mt-4">
                  <MiniBarChart values={[18, 22, 16, 24, 19]} />
                </div>
              </div>
            </div>
          </section>

          <section id="compras" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-text">Compras integradas</h2>
                <p className="mt-1 text-sm text-muted">Impacto no caixa e itens de maior custo.</p>
              </div>
              <StatusPill tone="warning">Custos em alta</StatusPill>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Compras semanais</p>
                <Sparkline values={[12, 18, 14, 20, 16, 22, 19]} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top itens</p>
                <div className="mt-4">
                  <MiniBarChart values={[9, 12, 8, 11, 7]} />
                </div>
              </div>
            </div>
          </section>

          <section id="producao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-text">Producao consolidada</h2>
                <p className="mt-1 text-sm text-muted">Planejado x produzido e perdas operacionais.</p>
              </div>
              <StatusPill tone="info">Rendimento 92%</StatusPill>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Volume produzido</p>
                <Sparkline values={[18, 20, 17, 22, 24, 21, 26]} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Perdas por etapa</p>
                <div className="mt-4">
                  <MiniBarChart values={[5, 4, 6, 3, 5]} />
                </div>
              </div>
            </div>
          </section>

          <section id="pedidos" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-text">Pedidos consolidados</h2>
                <p className="mt-1 text-sm text-muted">Status por periodo e ticket medio.</p>
              </div>
              <StatusPill tone="success">Conversao 78%</StatusPill>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos por dia</p>
                <Sparkline values={[20, 24, 22, 26, 28, 25, 30]} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Metodos de pagamento</p>
                <div className="mt-4">
                  <MiniBarChart values={[14, 10, 8, 12, 6]} />
                </div>
              </div>
            </div>
          </section>

          <section id="exportacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <h2 className="text-lg font-semibold text-text">Exportacao CSV</h2>
            <p className="mt-1 text-sm text-muted">
              Exporte relatorios consolidados para auditoria e analise gerencial.
            </p>
            <div className="mt-4 flex flex-wrap gap-2">
              <button
                type="button"
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
              >
                Exportar fluxo de caixa
              </button>
              <button
                type="button"
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Exportar compras
              </button>
              <button
                type="button"
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Exportar producao
              </button>
              <button
                type="button"
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Exportar pedidos
              </button>
            </div>
          </section>
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

import { StatusPill } from "@mrquentinha/ui";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { InventoryOpsPanel } from "@/components/modules/InventoryOpsPanel";

const MENU_ITEMS = [
  { label: "Visao geral", href: "#visao-geral" },
  { label: "Movimentos", href: "#movimentos" },
  { label: "Tendencias", href: "#tendencias" },
];

export default function EstoqueModulePage() {
  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Estoque"
          description="Controle de saldo, alertas de reposicao e rastreio de movimentos."
          statusLabel="Ativo"
          statusTone="success"
          menuItems={MENU_ITEMS}
        >
          <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-text">Visao geral</h2>
                <p className="mt-1 text-sm text-muted">Itens criticos e reposicao planejada.</p>
              </div>
              <StatusPill tone="warning">3 alertas</StatusPill>
            </div>
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Itens em alerta</p>
                <p className="mt-1 text-2xl font-semibold text-text">6</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Reposicoes hoje</p>
                <p className="mt-1 text-2xl font-semibold text-text">4</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Saldo total</p>
                <p className="mt-1 text-2xl font-semibold text-text">R$ 12.420</p>
              </article>
            </div>
          </section>

          <section id="movimentos" className="scroll-mt-24">
            <InventoryOpsPanel />
          </section>

          <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-lg font-semibold text-text">Tendencias de consumo</h2>
                <p className="mt-1 text-sm text-muted">Saidas diarias e reposicao planejada.</p>
              </div>
              <StatusPill tone="info">Cobertura 5 dias</StatusPill>
            </div>
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Consumo semanal</p>
                <Sparkline values={[10, 14, 12, 18, 16, 22, 19]} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Reposicoes por dia</p>
                <div className="mt-4">
                  <MiniBarChart values={[8, 12, 6, 10, 9]} />
                </div>
              </div>
            </div>
          </section>
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

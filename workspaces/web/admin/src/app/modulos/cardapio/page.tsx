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
import { MenuOpsPanel } from "@/components/modules/MenuOpsPanel";

const BASE_PATH = "/modulos/cardapio";

const MENU_ITEMS = [
  { key: "all", label: "Todos", href: BASE_PATH },
  { key: "planejamento", label: "Planejamento", href: `${BASE_PATH}?view=planejamento#planejamento` },
  { key: "menus", label: "Menus", href: `${BASE_PATH}?view=menus#menus` },
  { key: "tendencias", label: "Tendencias", href: `${BASE_PATH}?view=tendencias#tendencias` },
];

export default function CardapioModulePage() {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "all";
  const showAll = activeView === "all";

  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Cardapio"
          description="Planejamento de menus, pratos e volume esperado por dia."
          statusLabel="Baseline ativo"
          statusTone="info"
          menuItems={MENU_ITEMS}
          activeKey={activeView}
        >
          {(showAll || activeView === "planejamento") && (
            <section id="planejamento" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Planejamento do dia</h2>
                  <p className="mt-1 text-sm text-muted">Menus ativos e pratos mais demandados.</p>
                </div>
                <StatusPill tone="brand">Menu ativo</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Menus ativos</p>
                  <p className="mt-1 text-2xl font-semibold text-text">2</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pratos do dia</p>
                  <p className="mt-1 text-2xl font-semibold text-text">6</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Porcoes previstas</p>
                  <p className="mt-1 text-2xl font-semibold text-text">120</p>
                </article>
              </div>
            </section>
          )}

          {(showAll || activeView === "menus") && (
            <section id="menus" className="scroll-mt-24">
              <MenuOpsPanel />
            </section>
          )}

          {(showAll || activeView === "tendencias") && (
            <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Tendencias do cardapio</h2>
                  <p className="mt-1 text-sm text-muted">Demanda e sazonalidade por prato.</p>
                </div>
                <StatusPill tone="info">Demanda estavel</StatusPill>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Pedidos por prato</p>
                  <Sparkline values={[6, 10, 12, 9, 14, 11, 15]} className="mt-3" />
                </div>
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Top pratos</p>
                  <div className="mt-4">
                    <MiniBarChart values={[14, 10, 8, 12, 9]} />
                  </div>
                </div>
              </div>
            </section>
          )}
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

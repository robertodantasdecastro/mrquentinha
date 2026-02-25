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
import { UsersRbacPanel } from "@/components/modules/UsersRbacPanel";

const BASE_PATH = "/modulos/usuarios-rbac";

const MENU_ITEMS = [
  { key: "all", label: "Todos", href: BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${BASE_PATH}?view=visao-geral#visao-geral` },
  { key: "usuarios", label: "Usuarios", href: `${BASE_PATH}?view=usuarios#usuarios` },
  { key: "tendencias", label: "Tendencias", href: `${BASE_PATH}?view=tendencias#tendencias` },
];

export default function UsuariosRbacModulePage() {
  const searchParams = useSearchParams();
  const activeView = searchParams.get("view") || "all";
  const showAll = activeView === "all";

  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Usuarios e RBAC"
          description="Gestao de papeis, permissoes e trilha basica de auditoria."
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
                  <p className="mt-1 text-sm text-muted">Distribuicao de papeis e acessos criticos.</p>
                </div>
                <StatusPill tone="info">Roles ativos</StatusPill>
              </div>
              <div className="mt-4 grid gap-3 md:grid-cols-3">
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Usuarios ativos</p>
                  <p className="mt-1 text-2xl font-semibold text-text">8</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Admins</p>
                  <p className="mt-1 text-2xl font-semibold text-text">2</p>
                </article>
                <article className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Financeiro</p>
                  <p className="mt-1 text-2xl font-semibold text-text">1</p>
                </article>
              </div>
            </section>
          )}

          {(showAll || activeView === "usuarios") && (
            <section id="usuarios" className="scroll-mt-24">
              <UsersRbacPanel />
            </section>
          )}

          {(showAll || activeView === "tendencias") && (
            <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
              <div className="flex flex-wrap items-center justify-between gap-3">
                <div>
                  <h2 className="text-lg font-semibold text-text">Tendencias de acesso</h2>
                  <p className="mt-1 text-sm text-muted">Ativacoes recentes e distribuicao de roles.</p>
                </div>
                <StatusPill tone="brand">Engajamento 86%</StatusPill>
              </div>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ativacoes semanais</p>
                  <Sparkline values={[2, 4, 3, 5, 4, 6, 5]} className="mt-3" />
                </div>
                <div className="rounded-xl border border-border bg-bg p-4">
                  <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Distribuicao de roles</p>
                  <div className="mt-4">
                    <MiniBarChart values={[6, 3, 4, 2, 1]} />
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

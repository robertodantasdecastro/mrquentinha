import { StatusPill } from "@mrquentinha/ui";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { UsersRbacPanel } from "@/components/modules/UsersRbacPanel";

const MENU_ITEMS = [
  { label: "Visao geral", href: "#visao-geral" },
  { label: "Usuarios", href: "#usuarios" },
  { label: "Tendencias", href: "#tendencias" },
];

export default function UsuariosRbacModulePage() {
  return (
    <AdminSessionGate>
      {() => (
        <ModulePageShell
          title="Usuarios e RBAC"
          description="Gestao de papeis, permissoes e trilha basica de auditoria."
          statusLabel="Baseline ativo"
          statusTone="info"
          menuItems={MENU_ITEMS}
        >
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

          <section id="usuarios" className="scroll-mt-24">
            <UsersRbacPanel />
          </section>

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
        </ModulePageShell>
      )}
    </AdminSessionGate>
  );
}

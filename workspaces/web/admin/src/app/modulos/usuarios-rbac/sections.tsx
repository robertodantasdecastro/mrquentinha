"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { ApiError, listRolesAdmin, listUsersAdmin } from "@/lib/api";
import {
  buildRecentDateKeys,
  buildSeriesFromTotals,
  sumByDateKey,
} from "@/lib/metrics";
import type { AdminUserData, RoleData } from "@/types/api";

import { MiniBarChart } from "@/components/charts/MiniBarChart";
import { Sparkline } from "@/components/charts/Sparkline";
import { UsersRbacPanel } from "@/components/modules/UsersRbacPanel";

export const USUARIOS_RBAC_BASE_PATH = "/modulos/usuarios-rbac";

export const USUARIOS_RBAC_MENU_ITEMS = [
  { key: "all", label: "Todos", href: USUARIOS_RBAC_BASE_PATH },
  { key: "visao-geral", label: "Visao geral", href: `${USUARIOS_RBAC_BASE_PATH}/visao-geral#visao-geral` },
  { key: "usuarios", label: "Usuarios", href: `${USUARIOS_RBAC_BASE_PATH}/usuarios#usuarios` },
  { key: "tendencias", label: "Tendencias", href: `${USUARIOS_RBAC_BASE_PATH}/tendencias#tendencias` },
];

export type UsuariosRbacSectionKey =
  | "all"
  | "visao-geral"
  | "usuarios"
  | "tendencias";

type UsuariosRbacSectionsProps = {
  activeSection?: UsuariosRbacSectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar usuarios e RBAC.";
}

export function UsuariosRbacSections({ activeSection = "all" }: UsuariosRbacSectionsProps) {
  const [users, setUsers] = useState<AdminUserData[]>([]);
  const [roles, setRoles] = useState<RoleData[]>([]);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadUsuarios() {
      try {
        const [usersPayload, rolesPayload] = await Promise.all([
          listUsersAdmin(),
          listRolesAdmin(),
        ]);

        if (!mounted) {
          return;
        }

        setUsers(usersPayload);
        setRoles(rolesPayload.filter((role) => role.is_active));
        setErrorMessage("");
      } catch (error) {
        if (mounted) {
          setErrorMessage(resolveErrorMessage(error));
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadUsuarios();

    return () => {
      mounted = false;
    };
  }, []);

  const adminCount = useMemo(
    () => users.filter((user) => user.roles.includes("ADMIN")).length,
    [users],
  );

  const trendDateKeys = useMemo(() => buildRecentDateKeys(7), []);
  const usersByDate = useMemo(
    () => sumByDateKey(users, (user) => user.date_joined, () => 1),
    [users],
  );
  const usersSeries = useMemo(() => {
    const values = buildSeriesFromTotals(trendDateKeys, usersByDate);
    return values.length > 0 ? values : [0, 0];
  }, [trendDateKeys, usersByDate]);

  const roleValues = useMemo(() => {
    const totals: Record<string, number> = {};
    for (const user of users) {
      for (const roleCode of user.roles) {
        totals[roleCode] = (totals[roleCode] ?? 0) + 1;
      }
    }

    const values = Object.values(totals)
      .sort((a, b) => b - a)
      .slice(0, 5);

    return values.length > 0 ? values : [0, 0, 0];
  }, [users]);

  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "visao-geral") && (
        <section id="visao-geral" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Visao geral</h2>
              <p className="mt-1 text-sm text-muted">Distribuicao de papeis e acessos criticos.</p>
            </div>
            <StatusPill tone="info">Roles ativos</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando resumo de usuarios...</p>}
          {!loading && (
            <div className="mt-4 grid gap-3 md:grid-cols-3">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Usuarios ativos</p>
                <p className="mt-1 text-2xl font-semibold text-text">{users.length}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Admins</p>
                <p className="mt-1 text-2xl font-semibold text-text">{adminCount}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Papeis ativos</p>
                <p className="mt-1 text-2xl font-semibold text-text">{roles.length}</p>
              </article>
            </div>
          )}
        </section>
      )}

      {(showAll || activeSection === "usuarios") && (
        <section id="usuarios" className="scroll-mt-24">
          <UsersRbacPanel />
        </section>
      )}

      {(showAll || activeSection === "tendencias") && (
        <section id="tendencias" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Tendencias de acesso</h2>
              <p className="mt-1 text-sm text-muted">Ativacoes recentes e distribuicao de roles.</p>
            </div>
            <StatusPill tone="brand">Usuarios ativos</StatusPill>
          </div>
          {loading && <p className="mt-3 text-sm text-muted">Carregando tendencias...</p>}
          {!loading && (
            <div className="mt-4 grid gap-4 md:grid-cols-2">
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ativacoes semanais</p>
                <Sparkline values={usersSeries} className="mt-3" />
              </div>
              <div className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Distribuicao de roles</p>
                <div className="mt-4">
                  <MiniBarChart values={roleValues} />
                </div>
              </div>
            </div>
          )}
        </section>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-border bg-bg px-4 py-3 text-sm text-rose-600">
          {errorMessage}
        </div>
      )}
    </>
  );
}

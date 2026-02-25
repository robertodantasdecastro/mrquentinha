"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import {
  ApiError,
  assignUserRolesAdmin,
  listRolesAdmin,
  listUsersAdmin,
} from "@/lib/api";
import type { AdminUserData, RoleData } from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar modulo de Usuarios/RBAC.";
}

function formatDateTime(valueRaw: string): string {
  const dateValue = new Date(valueRaw);
  if (Number.isNaN(dateValue.getTime())) {
    return valueRaw;
  }

  return dateValue.toLocaleString("pt-BR");
}

function resolveActiveTone(isActive: boolean): StatusTone {
  return isActive ? "success" : "danger";
}

export function UsersRbacPanel() {
  const [users, setUsers] = useState<AdminUserData[]>([]);
  const [roles, setRoles] = useState<RoleData[]>([]);
  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedRoleCodes, setSelectedRoleCodes] = useState<string[]>([]);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [saving, setSaving] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");

  async function loadUsersRbac({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [usersPayload, rolesPayload] = await Promise.all([
        listUsersAdmin(),
        listRolesAdmin(),
      ]);

      setUsers(usersPayload);
      setRoles(rolesPayload.filter((role) => role.is_active));

      if (usersPayload.length > 0) {
        const parsedSelectedId = Number.parseInt(selectedUserId, 10);
        const selectedUser =
          usersPayload.find((user) => user.id === parsedSelectedId) ?? usersPayload[0];

        setSelectedUserId(String(selectedUser.id));
        setSelectedRoleCodes(selectedUser.roles);
      } else {
        setSelectedUserId("");
        setSelectedRoleCodes([]);
      }

      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }

  useEffect(() => {
    void loadUsersRbac();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const selectedUser = useMemo(() => {
    const parsedId = Number.parseInt(selectedUserId, 10);
    if (Number.isNaN(parsedId)) {
      return null;
    }

    return users.find((user) => user.id === parsedId) ?? null;
  }, [selectedUserId, users]);

  const adminUsersCount = useMemo(
    () => users.filter((user) => user.roles.includes("ADMIN")).length,
    [users],
  );

  function handleSelectUser(user: AdminUserData) {
    setSelectedUserId(String(user.id));
    setSelectedRoleCodes(user.roles);
    setMessage("");
    setErrorMessage("");
  }

  function toggleRole(code: string) {
    setSelectedRoleCodes((previous) => {
      if (previous.includes(code)) {
        return previous.filter((item) => item !== code);
      }

      return [...previous, code].sort();
    });
  }

  async function handleSaveRoles() {
    if (!selectedUser) {
      setErrorMessage("Selecione um usuario para atualizar papeis.");
      return;
    }

    if (selectedRoleCodes.length === 0) {
      setErrorMessage("Selecione ao menos um papel para o usuario.");
      return;
    }

    setSaving(true);
    setMessage("");
    setErrorMessage("");

    try {
      const result = await assignUserRolesAdmin(selectedUser.id, {
        role_codes: selectedRoleCodes,
        replace: true,
      });

      setMessage(
        `Papeis de ${result.username} atualizados: ${result.role_codes.join(", ")}.`,
      );
      await loadUsersRbac({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Usuarios e RBAC</h3>
          <p className="text-sm text-muted">
            Gestao de papeis por usuario com escopo administrativo (ADMIN).
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadUsersRbac({ silent: true })}
          disabled={refreshing || loading}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          {refreshing ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {loading && <p className="mt-4 text-sm text-muted">Carregando modulo de Usuarios/RBAC...</p>}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-3">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Usuarios</p>
              <p className="mt-1 text-2xl font-semibold text-text">{users.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Com ADMIN</p>
              <p className="mt-1 text-2xl font-semibold text-text">{adminUsersCount}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Papeis ativos</p>
              <p className="mt-1 text-2xl font-semibold text-text">{roles.length}</p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Usuarios</h4>
              {users.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhum usuario encontrado.</p>
              )}
              {users.length > 0 && (
                <div className="mt-3 space-y-2">
                  {users.map((user) => {
                    const isSelected = selectedUser?.id === user.id;

                    return (
                      <article
                        key={user.id}
                        className={`rounded-lg border px-3 py-2 ${
                          isSelected
                            ? "border-primary bg-primary/5"
                            : "border-border bg-surface"
                        }`}
                      >
                        <div className="flex items-start justify-between gap-2">
                          <div>
                            <p className="text-sm font-semibold text-text">{user.username}</p>
                            <div className="flex items-center gap-2 text-xs text-muted">
                              <p>{user.email || "sem e-mail"}</p>
                              <StatusPill tone={resolveActiveTone(user.is_active)}>
                                {user.is_active ? "ativo" : "inativo"}
                              </StatusPill>
                            </div>
                            <p className="text-xs text-muted">
                              cadastro: {formatDateTime(user.date_joined)}
                            </p>
                          </div>
                          <button
                            type="button"
                            onClick={() => handleSelectUser(user)}
                            className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                          >
                            {isSelected ? "Selecionado" : "Selecionar"}
                          </button>
                        </div>
                        <p className="mt-2 text-xs text-muted">
                          Papeis: {user.roles.length > 0 ? user.roles.join(", ") : "sem papeis"}
                        </p>
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Atribuicao de papeis</h4>
              {!selectedUser && (
                <p className="mt-3 text-sm text-muted">
                  Selecione um usuario para editar papeis.
                </p>
              )}

              {selectedUser && (
                <div className="mt-3 space-y-3">
                  <p className="text-sm text-muted">
                    Editando papeis de <strong className="text-text">{selectedUser.username}</strong>.
                  </p>

                  <div className="space-y-2">
                    {roles.map((role) => {
                      const checked = selectedRoleCodes.includes(role.code);

                      return (
                        <label
                          key={role.id}
                          className="flex items-start gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm"
                        >
                          <input
                            type="checkbox"
                            checked={checked}
                            onChange={() => toggleRole(role.code)}
                            className="mt-0.5 h-4 w-4"
                          />
                          <span>
                            <span className="font-semibold text-text">{role.code}</span>
                            <span className="block text-xs text-muted">{role.description}</span>
                          </span>
                        </label>
                      );
                    })}
                  </div>

                  <div className="flex justify-end">
                    <button
                      type="button"
                      onClick={() => void handleSaveRoles()}
                      disabled={saving || roles.length === 0}
                      className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                    >
                      {saving ? "Salvando..." : "Salvar papeis"}
                    </button>
                  </div>
                </div>
              )}
            </section>
          </div>
        </>
      )}

      {message && (
        <div className="mt-4 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {message}
        </div>
      )}

      {errorMessage && (
        <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          <p className="text-rose-600">{errorMessage}</p>
        </div>
      )}
    </section>
  );
}

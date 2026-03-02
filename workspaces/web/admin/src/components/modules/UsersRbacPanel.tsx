"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";
import { InlinePreloader } from "@/components/InlinePreloader";

import {
  ApiError,
  assignUserRolesAdmin,
  assignUserTasksAdmin,
  createUserAdmin,
  listRolesAdmin,
  listTaskCategoriesAdmin,
  listUsersAdmin,
  updateUserAdmin,
} from "@/lib/api";
import type { AdminUserData, RoleData, TaskCategoryData } from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar módulo de Usuários/RBAC.";
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

function resolveComplianceTone(isComplete: boolean): StatusTone {
  return isComplete ? "success" : "warning";
}

const MISSING_FIELD_LABELS: Record<string, string> = {
  email: "e-mail",
  full_name: "nome completo",
  phone: "telefone",
  postal_code: "CEP",
  street: "logradouro",
  street_number: "numero",
  neighborhood: "bairro",
  city: "cidade",
  state: "estado",
  cpf_ou_cnpj: "CPF/CNPJ",
  email_verificado: "e-mail confirmado",
};

type UserCreateFormState = {
  username: string;
  password: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
};

type UserEditFormState = {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  is_active: boolean;
  is_staff: boolean;
  password: string;
};

const CREATE_FORM_INITIAL_STATE: UserCreateFormState = {
  username: "",
  password: "",
  email: "",
  first_name: "",
  last_name: "",
  is_active: true,
  is_staff: false,
};

function formatMissingFields(fields: string[]): string {
  return fields
    .map((field) => MISSING_FIELD_LABELS[field] ?? field)
    .join(", ");
}

function toUserEditForm(user: AdminUserData): UserEditFormState {
  return {
    username: user.username,
    email: user.email || "",
    first_name: user.first_name || "",
    last_name: user.last_name || "",
    is_active: user.is_active,
    is_staff: user.is_staff,
    password: "",
  };
}

function toggleCode(code: string, current: string[]): string[] {
  if (current.includes(code)) {
    return current.filter((item) => item !== code);
  }

  return [...current, code].sort();
}

function hasStrongPassword(value: string): boolean {
  const password = String(value || "");
  const hasLower = /[a-z]/.test(password);
  const hasUpper = /[A-Z]/.test(password);
  const hasDigit = /\d/.test(password);
  return password.length >= 8 && hasLower && hasUpper && hasDigit;
}

export function UsersRbacPanel() {
  const [users, setUsers] = useState<AdminUserData[]>([]);
  const [roles, setRoles] = useState<RoleData[]>([]);
  const [taskCategories, setTaskCategories] = useState<TaskCategoryData[]>([]);

  const [selectedUserId, setSelectedUserId] = useState<string>("");
  const [selectedRoleCodes, setSelectedRoleCodes] = useState<string[]>([]);
  const [selectedTaskCodes, setSelectedTaskCodes] = useState<string[]>([]);

  const [createForm, setCreateForm] = useState<UserCreateFormState>(CREATE_FORM_INITIAL_STATE);
  const [createRoleCodes, setCreateRoleCodes] = useState<string[]>(["CLIENTE"]);
  const [createTaskCodes, setCreateTaskCodes] = useState<string[]>([]);

  const [editForm, setEditForm] = useState<UserEditFormState | null>(null);

  const [loading, setLoading] = useState<boolean>(true);
  const [refreshing, setRefreshing] = useState<boolean>(false);
  const [savingRoles, setSavingRoles] = useState<boolean>(false);
  const [savingTasks, setSavingTasks] = useState<boolean>(false);
  const [creatingUser, setCreatingUser] = useState<boolean>(false);
  const [updatingUser, setUpdatingUser] = useState<boolean>(false);
  const [message, setMessage] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string>("");
  const editSectionRef = useRef<HTMLElement | null>(null);
  const rolesSectionRef = useRef<HTMLElement | null>(null);
  const tasksSectionRef = useRef<HTMLElement | null>(null);
  const createSectionRef = useRef<HTMLElement | null>(null);

  async function loadUsersRbac({ silent = false }: { silent?: boolean } = {}) {
    if (silent) {
      setRefreshing(true);
    } else {
      setLoading(true);
    }

    try {
      const [usersPayload, rolesPayload, taskCategoriesPayload] = await Promise.all([
        listUsersAdmin(),
        listRolesAdmin(),
        listTaskCategoriesAdmin(),
      ]);

      setUsers(usersPayload);
      setRoles(rolesPayload.filter((role) => role.is_active));
      setTaskCategories(taskCategoriesPayload.filter((category) => category.is_active));

      if (usersPayload.length > 0) {
        const parsedSelectedId = Number.parseInt(selectedUserId, 10);
        const selectedUser =
          usersPayload.find((user) => user.id === parsedSelectedId) ?? usersPayload[0];

        setSelectedUserId(String(selectedUser.id));
        setSelectedRoleCodes(selectedUser.roles);
        setSelectedTaskCodes(selectedUser.task_codes || []);
        setEditForm(toUserEditForm(selectedUser));
      } else {
        setSelectedUserId("");
        setSelectedRoleCodes([]);
        setSelectedTaskCodes([]);
        setEditForm(null);
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
  const verifiedEmailCount = useMemo(
    () => users.filter((user) => user.email_verified).length,
    [users],
  );
  const essentialCompleteCount = useMemo(
    () => users.filter((user) => user.essential_profile_complete).length,
    [users],
  );

  function scrollToSection(section: "edit" | "roles" | "tasks" | "create") {
    const refs = {
      edit: editSectionRef,
      roles: rolesSectionRef,
      tasks: tasksSectionRef,
      create: createSectionRef,
    } as const;

    window.requestAnimationFrame(() => {
      refs[section].current?.scrollIntoView({
        behavior: "smooth",
        block: "start",
      });
    });
  }

  function handleSelectUser(user: AdminUserData, options?: { focusSection?: "edit" | "roles" | "tasks" }) {
    setSelectedUserId(String(user.id));
    setSelectedRoleCodes(user.roles);
    setSelectedTaskCodes(user.task_codes || []);
    setEditForm(toUserEditForm(user));
    setMessage("");
    setErrorMessage("");
    if (options?.focusSection) {
      scrollToSection(options.focusSection);
    }
  }

  async function handleCreateUser() {
    if (!createForm.username.trim()) {
      setErrorMessage("Informe o nome de usuário para criação.");
      return;
    }

    if (!hasStrongPassword(createForm.password)) {
      setErrorMessage(
        "Senha inicial invalida. Use ao menos 8 caracteres com letra maiuscula, minuscula e numero.",
      );
      return;
    }

    if (createRoleCodes.length === 0) {
      setErrorMessage("Selecione ao menos um papel para o novo usuário.");
      return;
    }

    setCreatingUser(true);
    setMessage("");
    setErrorMessage("");

    try {
      const created = await createUserAdmin({
        username: createForm.username.trim(),
        password: createForm.password,
        email: createForm.email.trim(),
        first_name: createForm.first_name.trim(),
        last_name: createForm.last_name.trim(),
        is_active: createForm.is_active,
        is_staff: createForm.is_staff,
        role_codes: createRoleCodes,
        task_codes: createTaskCodes,
      });

      setCreateForm(CREATE_FORM_INITIAL_STATE);
      setCreateRoleCodes(["CLIENTE"]);
      setCreateTaskCodes([]);
      setSelectedUserId(String(created.id));
      setMessage(`Usuário ${created.username} criado com sucesso.`);
      await loadUsersRbac({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCreatingUser(false);
    }
  }

  async function handleUpdateUser() {
    if (!selectedUser || !editForm) {
      setErrorMessage("Selecione um usuário para edição cadastral.");
      return;
    }

    if (!editForm.username.trim()) {
      setErrorMessage("O nome de usuário não pode ficar vazio.");
      return;
    }

    if (editForm.password.trim() && !hasStrongPassword(editForm.password)) {
      setErrorMessage(
        "Nova senha invalida. Use ao menos 8 caracteres com letra maiuscula, minuscula e numero.",
      );
      return;
    }

    setUpdatingUser(true);
    setMessage("");
    setErrorMessage("");

    try {
      const payload: Record<string, unknown> = {
        username: editForm.username.trim(),
        email: editForm.email.trim(),
        first_name: editForm.first_name.trim(),
        last_name: editForm.last_name.trim(),
        is_active: editForm.is_active,
        is_staff: editForm.is_staff,
      };
      if (editForm.password.trim()) {
        payload.password = editForm.password;
      }

      const result = await updateUserAdmin(selectedUser.id, payload);
      setMessage(`Conta de ${result.username} atualizada com sucesso.`);
      await loadUsersRbac({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUpdatingUser(false);
    }
  }

  async function handleSaveRoles() {
    if (!selectedUser) {
      setErrorMessage("Selecione um usuário para atualizar papéis.");
      return;
    }

    if (selectedRoleCodes.length === 0) {
      setErrorMessage("Selecione ao menos um papel para o usuário.");
      return;
    }

    setSavingRoles(true);
    setMessage("");
    setErrorMessage("");

    try {
      const result = await assignUserRolesAdmin(selectedUser.id, {
        role_codes: selectedRoleCodes,
        replace: true,
      });

      setMessage(`Papéis de ${result.username} atualizados: ${result.role_codes.join(", ")}.`);
      await loadUsersRbac({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingRoles(false);
    }
  }

  async function handleSaveTasks() {
    if (!selectedUser) {
      setErrorMessage("Selecione um usuário para atualizar tarefas.");
      return;
    }

    setSavingTasks(true);
    setMessage("");
    setErrorMessage("");

    try {
      const result = await assignUserTasksAdmin(selectedUser.id, {
        task_codes: selectedTaskCodes,
        replace: true,
      });

      setMessage(`Tarefas de ${result.username} atualizadas: ${result.task_codes.join(", ") || "nenhuma"}.`);
      await loadUsersRbac({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingTasks(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Usuários, RBAC e Tarefas</h3>
          <p className="text-sm text-muted">
            Gestão completa de contas, papéis, categorias e tarefas operacionais.
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

      {loading && <InlinePreloader message="Carregando módulo de Usuários/RBAC..." className="mt-4 justify-start bg-surface/70" />}

      {!loading && (
        <>
          <div className="mt-4 grid gap-3 sm:grid-cols-2 xl:grid-cols-6">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Usuários</p>
              <p className="mt-1 text-2xl font-semibold text-text">{users.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Com ADMIN</p>
              <p className="mt-1 text-2xl font-semibold text-text">{adminUsersCount}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Papéis ativos</p>
              <p className="mt-1 text-2xl font-semibold text-text">{roles.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Categorias de tarefa</p>
              <p className="mt-1 text-2xl font-semibold text-text">{taskCategories.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">E-mails verificados</p>
              <p className="mt-1 text-2xl font-semibold text-text">{verifiedEmailCount}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Perfil essencial ok</p>
              <p className="mt-1 text-2xl font-semibold text-text">{essentialCompleteCount}</p>
            </article>
          </div>

          <div className="mt-4 grid gap-4 xl:grid-cols-[1.1fr,1.3fr]">
            <section className="rounded-xl border border-border bg-bg p-4">
              <div className="flex items-center justify-between gap-2">
                <h4 className="text-base font-semibold text-text">Usuários</h4>
                <button
                  type="button"
                  onClick={() => scrollToSection("create")}
                  className="rounded-md border border-border bg-surface px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                >
                  Nova conta
                </button>
              </div>
              {users.length === 0 && (
                <p className="mt-3 text-sm text-muted">Nenhum usuário encontrado.</p>
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
                            <div className="flex flex-wrap items-center gap-2 text-xs text-muted">
                              <p>{user.email || "sem e-mail"}</p>
                              <StatusPill tone={resolveActiveTone(user.is_active)}>
                                {user.is_active ? "ativo" : "inativo"}
                              </StatusPill>
                              <StatusPill tone={user.email_verified ? "success" : "warning"}>
                                {user.email_verified ? "email ok" : "email pendente"}
                              </StatusPill>
                              <StatusPill tone={resolveComplianceTone(user.essential_profile_complete)}>
                                {user.essential_profile_complete ? "perfil completo" : "perfil incompleto"}
                              </StatusPill>
                              <StatusPill tone={user.can_access_technical_admin ? "info" : "neutral"}>
                                {user.can_access_technical_admin ? "acesso técnico" : "sem acesso técnico"}
                              </StatusPill>
                            </div>
                            <p className="text-xs text-muted">
                              cadastro: {formatDateTime(user.date_joined)}
                            </p>
                            {user.email_verification_last_sent_at && (
                              <p className="text-xs text-muted">
                                ultimo envio de confirmacao:{" "}
                                {formatDateTime(user.email_verification_last_sent_at)}
                              </p>
                            )}
                          </div>
                          <button
                            type="button"
                            onClick={() => handleSelectUser(user, { focusSection: "edit" })}
                            className="rounded-md border border-border bg-bg px-3 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                          >
                            {isSelected ? "Editando" : "Editar conta"}
                          </button>
                        </div>
                        <p className="mt-2 text-xs text-muted">
                          Papéis: {user.roles.length > 0 ? user.roles.join(", ") : "sem papéis"}
                        </p>
                        <p className="mt-1 text-xs text-muted">
                          Tarefas: {user.task_codes.length > 0 ? user.task_codes.join(", ") : "sem tarefas"}
                        </p>
                        {!user.essential_profile_complete && (
                          <p className="mt-1 text-xs text-amber-600 dark:text-amber-300">
                            Pendencias: {formatMissingFields(user.missing_essential_profile_fields)}
                          </p>
                        )}
                      </article>
                    );
                  })}
                </div>
              )}
            </section>

            <section className="space-y-4">
              <article className="rounded-xl border border-border bg-bg p-4">
                <h4 className="text-base font-semibold text-text">Assistente de fluxo</h4>
                <p className="mt-1 text-sm text-muted">
                  Selecione um usuário na lista e siga os blocos em ordem para reduzir erros operacionais.
                </p>
                <div className="mt-3 grid gap-2 sm:grid-cols-2">
                  <button
                    type="button"
                    onClick={() => scrollToSection("edit")}
                    disabled={!selectedUser}
                    className="rounded-md border border-border bg-surface px-3 py-2 text-left text-sm text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    1. Editar conta selecionada
                  </button>
                  <button
                    type="button"
                    onClick={() => scrollToSection("roles")}
                    disabled={!selectedUser}
                    className="rounded-md border border-border bg-surface px-3 py-2 text-left text-sm text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    2. Ajustar papéis (RBAC)
                  </button>
                  <button
                    type="button"
                    onClick={() => scrollToSection("tasks")}
                    disabled={!selectedUser}
                    className="rounded-md border border-border bg-surface px-3 py-2 text-left text-sm text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    3. Ajustar tarefas operacionais
                  </button>
                  <button
                    type="button"
                    onClick={() => scrollToSection("create")}
                    className="rounded-md border border-border bg-surface px-3 py-2 text-left text-sm text-text transition hover:border-primary hover:text-primary"
                  >
                    4. Criar nova conta
                  </button>
                </div>
              </article>

              <article ref={editSectionRef} className="rounded-xl border border-border bg-bg p-4">
                <h4 className="text-base font-semibold text-text">Edição da conta selecionada</h4>
                {!selectedUser || !editForm ? (
                  <p className="mt-3 text-sm text-muted">Selecione um usuário para editar conta, papéis e tarefas.</p>
                ) : (
                  <>
                    <div className="mt-3 grid gap-3 md:grid-cols-2">
                      <label className="text-sm text-muted">
                        Usuário
                        <input
                          value={editForm.username}
                          onChange={(event) => {
                            const username = event.currentTarget.value;
                            setEditForm((current) => (current ? { ...current, username } : current));
                          }}
                          className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                        />
                      </label>
                      <label className="text-sm text-muted">
                        E-mail
                        <input
                          type="email"
                          value={editForm.email}
                          onChange={(event) => {
                            const email = event.currentTarget.value;
                            setEditForm((current) => (current ? { ...current, email } : current));
                          }}
                          className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                        />
                      </label>
                      <label className="text-sm text-muted">
                        Nome
                        <input
                          value={editForm.first_name}
                          onChange={(event) => {
                            const first_name = event.currentTarget.value;
                            setEditForm((current) => (current ? { ...current, first_name } : current));
                          }}
                          className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                        />
                      </label>
                      <label className="text-sm text-muted">
                        Sobrenome
                        <input
                          value={editForm.last_name}
                          onChange={(event) => {
                            const last_name = event.currentTarget.value;
                            setEditForm((current) => (current ? { ...current, last_name } : current));
                          }}
                          className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                        />
                      </label>
                      <label className="text-sm text-muted md:col-span-2">
                        Nova senha (opcional)
                        <input
                          type="password"
                          value={editForm.password}
                          onChange={(event) => {
                            const password = event.currentTarget.value;
                            setEditForm((current) => (current ? { ...current, password } : current));
                          }}
                          className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                        />
                      </label>
                    </div>

                    <div className="mt-3 flex flex-wrap gap-3 text-sm text-muted">
                      <label className="inline-flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={editForm.is_active}
                          onChange={(event) => {
                            const is_active = event.currentTarget.checked;
                            setEditForm((current) => (current ? { ...current, is_active } : current));
                          }}
                        />
                        Ativo
                      </label>
                      <label className="inline-flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={editForm.is_staff}
                          onChange={(event) => {
                            const is_staff = event.currentTarget.checked;
                            setEditForm((current) => (current ? { ...current, is_staff } : current));
                          }}
                        />
                        Staff Django
                      </label>
                    </div>

                    <div className="mt-4 flex justify-end">
                      <button
                        type="button"
                        onClick={() => void handleUpdateUser()}
                        disabled={updatingUser}
                        className="rounded-md border border-primary bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition hover:bg-primary hover:text-white disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        {updatingUser ? "Salvando conta..." : "Salvar conta"}
                      </button>
                    </div>
                  </>
                )}
              </article>

              <article ref={rolesSectionRef} className="rounded-xl border border-border bg-bg p-4">
                <h4 className="text-base font-semibold text-text">Papéis e permissões</h4>
                {!selectedUser && (
                  <p className="mt-3 text-sm text-muted">
                    Selecione um usuário para editar papéis.
                  </p>
                )}

                {selectedUser && (
                  <div className="mt-3 space-y-3">
                    <p className="text-sm text-muted">
                      Editando papéis de <strong className="text-text">{selectedUser.username}</strong>.
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
                              onChange={() =>
                                setSelectedRoleCodes((current) => toggleCode(role.code, current))
                              }
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
                        disabled={savingRoles || roles.length === 0}
                        className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        {savingRoles ? "Salvando papéis..." : "Salvar papéis"}
                      </button>
                    </div>
                  </div>
                )}
              </article>

              <article ref={tasksSectionRef} className="rounded-xl border border-border bg-bg p-4">
                <h4 className="text-base font-semibold text-text">Categorias e tarefas</h4>
                {!selectedUser && (
                  <p className="mt-3 text-sm text-muted">
                    Selecione um usuário para atribuir tarefas operacionais.
                  </p>
                )}

                {selectedUser && (
                  <div className="mt-3 space-y-3">
                    <p className="text-sm text-muted">
                      Tarefas de <strong className="text-text">{selectedUser.username}</strong>.
                    </p>
                    <div className="space-y-2">
                      {taskCategories.map((category) => (
                        <div key={category.id} className="rounded-lg border border-border bg-surface p-3">
                          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                            {category.name}
                          </p>
                          <p className="mt-1 text-xs text-muted">{category.description}</p>
                          <div className="mt-2 space-y-1.5">
                            {category.tasks
                              .filter((task) => task.is_active)
                              .map((task) => {
                                const checked = selectedTaskCodes.includes(task.code);
                                return (
                                  <label key={task.id} className="flex items-start gap-2 text-sm text-text">
                                    <input
                                      type="checkbox"
                                      checked={checked}
                                      onChange={() =>
                                        setSelectedTaskCodes((current) => toggleCode(task.code, current))
                                      }
                                      className="mt-0.5 h-4 w-4"
                                    />
                                    <span>
                                      <span>{task.name}</span>
                                      <span className="block text-xs text-muted">
                                        {task.description}
                                      </span>
                                    </span>
                                  </label>
                                );
                              })}
                          </div>
                        </div>
                      ))}
                    </div>

                    <div className="flex justify-end">
                      <button
                        type="button"
                        onClick={() => void handleSaveTasks()}
                        disabled={savingTasks || taskCategories.length === 0}
                        className="rounded-md border border-primary bg-primary/10 px-4 py-2 text-sm font-semibold text-primary transition hover:bg-primary hover:text-white disabled:cursor-not-allowed disabled:opacity-70"
                      >
                        {savingTasks ? "Salvando tarefas..." : "Salvar tarefas"}
                      </button>
                    </div>
                  </div>
                )}
              </article>
              <article ref={createSectionRef} className="rounded-xl border border-border bg-bg p-4">
                <h4 className="text-base font-semibold text-text">Criar conta de usuário</h4>
                <div className="mt-3 grid gap-3 md:grid-cols-2">
                  <label className="text-sm text-muted">
                    Usuário
                    <input
                      value={createForm.username}
                      onChange={(event) => {
                        const username = event.currentTarget.value;
                        setCreateForm((current) => ({ ...current, username }));
                      }}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="text-sm text-muted">
                    Senha inicial
                    <input
                      type="password"
                      value={createForm.password}
                      onChange={(event) => {
                        const password = event.currentTarget.value;
                        setCreateForm((current) => ({ ...current, password }));
                      }}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="text-sm text-muted">
                    E-mail
                    <input
                      type="email"
                      value={createForm.email}
                      onChange={(event) => {
                        const email = event.currentTarget.value;
                        setCreateForm((current) => ({ ...current, email }));
                      }}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="text-sm text-muted">
                    Nome
                    <input
                      value={createForm.first_name}
                      onChange={(event) => {
                        const first_name = event.currentTarget.value;
                        setCreateForm((current) => ({ ...current, first_name }));
                      }}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="text-sm text-muted">
                    Sobrenome
                    <input
                      value={createForm.last_name}
                      onChange={(event) => {
                        const last_name = event.currentTarget.value;
                        setCreateForm((current) => ({ ...current, last_name }));
                      }}
                      className="mt-1 w-full rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                </div>

                <div className="mt-3 flex flex-wrap gap-3 text-sm text-muted">
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={createForm.is_active}
                      onChange={(event) => {
                        const is_active = event.currentTarget.checked;
                        setCreateForm((current) => ({ ...current, is_active }));
                      }}
                    />
                    Ativo
                  </label>
                  <label className="inline-flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={createForm.is_staff}
                      onChange={(event) => {
                        const is_staff = event.currentTarget.checked;
                        setCreateForm((current) => ({ ...current, is_staff }));
                      }}
                    />
                    Staff Django
                  </label>
                </div>

                <div className="mt-4 grid gap-3 lg:grid-cols-2">
                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Papéis iniciais</p>
                    <div className="mt-2 space-y-2">
                      {roles.map((role) => (
                        <label
                          key={`create-role-${role.id}`}
                          className="flex items-start gap-2 rounded-lg border border-border bg-surface px-3 py-2 text-sm"
                        >
                          <input
                            type="checkbox"
                            checked={createRoleCodes.includes(role.code)}
                            onChange={() => setCreateRoleCodes((current) => toggleCode(role.code, current))}
                            className="mt-0.5 h-4 w-4"
                          />
                          <span>
                            <span className="font-semibold text-text">{role.code}</span>
                            <span className="block text-xs text-muted">{role.description}</span>
                          </span>
                        </label>
                      ))}
                    </div>
                  </div>

                  <div>
                    <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Tarefas iniciais</p>
                    <div className="mt-2 max-h-52 space-y-2 overflow-y-auto pr-1">
                      {taskCategories.map((category) => (
                        <div key={`create-task-category-${category.id}`} className="rounded-lg border border-border bg-surface p-2">
                          <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">{category.name}</p>
                          <div className="mt-2 space-y-1.5">
                            {category.tasks
                              .filter((task) => task.is_active)
                              .map((task) => (
                                <label key={`create-task-${task.id}`} className="flex items-start gap-2 text-xs text-text">
                                  <input
                                    type="checkbox"
                                    checked={createTaskCodes.includes(task.code)}
                                    onChange={() => setCreateTaskCodes((current) => toggleCode(task.code, current))}
                                    className="mt-0.5 h-3.5 w-3.5"
                                  />
                                  <span>{task.name}</span>
                                </label>
                              ))}
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="mt-4 flex justify-end">
                  <button
                    type="button"
                    onClick={() => void handleCreateUser()}
                    disabled={creatingUser}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {creatingUser ? "Criando..." : "Criar usuário"}
                  </button>
                </div>
              </article>
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

"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  copyPortalDatabaseBackupToDevViaScpAdmin,
  createPortalDatabaseBackupAdmin,
  executePortalDatabasePsqlAdmin,
  fetchPortalDatabaseCommandCatalogAdmin,
  listPortalDatabaseBackupsAdmin,
  managePortalDatabaseTunnelAdmin,
  restorePortalDatabaseBackupAdmin,
  runPortalDatabaseDjangoDbbackupAdmin,
  savePortalDatabaseTunnelAdmin,
  syncPortalDatabaseToDevAdmin,
  syncPortalDatabaseViaDjangoAdmin,
} from "@/lib/api";
import type { PortalDatabaseBackupItem, PortalDatabaseTunnelState } from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada na operacao de banco.";
}

function formatBytes(value: number): string {
  if (!value || value < 1) {
    return "0 B";
  }
  const units = ["B", "KB", "MB", "GB"];
  let index = 0;
  let current = value;
  while (current >= 1024 && index < units.length - 1) {
    current /= 1024;
    index += 1;
  }
  return `${current.toFixed(index === 0 ? 0 : 2)} ${units[index]}`;
}

function formatDate(value: string): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("pt-BR");
}

function defaultTunnelState(): PortalDatabaseTunnelState {
  return {
    enabled: false,
    local_bind_host: "127.0.0.1",
    local_port: 55432,
    remote_db_host: "127.0.0.1",
    remote_db_port: 5432,
    status: "inactive",
    pid: null,
    last_started_at: "",
    last_stopped_at: "",
    last_error: "",
  };
}

export function DatabaseOpsPanel() {
  const [activeStep, setActiveStep] = useState<"tunnel" | "psql" | "backup" | "django" | "commands">(
    "tunnel",
  );
  const [loading, setLoading] = useState(true);
  const [creating, setCreating] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [syncing, setSyncing] = useState(false);
  const [scpCopying, setScpCopying] = useState(false);
  const [tunnelBusy, setTunnelBusy] = useState(false);
  const [psqlBusy, setPsqlBusy] = useState(false);
  const [djangoBusy, setDjangoBusy] = useState(false);
  const [dbbackupBusy, setDbbackupBusy] = useState(false);
  const [label, setLabel] = useState("manual");
  const [confirmRestore, setConfirmRestore] = useState("");
  const [selectedBackup, setSelectedBackup] = useState("");
  const [backups, setBackups] = useState<PortalDatabaseBackupItem[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<string | null>(null);

  const [tunnelState, setTunnelState] = useState<PortalDatabaseTunnelState>(defaultTunnelState());
  const [tunnelBindHost, setTunnelBindHost] = useState("127.0.0.1");
  const [tunnelLocalPort, setTunnelLocalPort] = useState("55432");
  const [tunnelRemoteHost, setTunnelRemoteHost] = useState("127.0.0.1");
  const [tunnelRemotePort, setTunnelRemotePort] = useState("5432");

  const [psqlCommand, setPsqlCommand] = useState("SELECT now();");
  const [psqlReadOnly, setPsqlReadOnly] = useState(true);
  const [psqlConfirm, setPsqlConfirm] = useState("");
  const [psqlOutput, setPsqlOutput] = useState("");

  const [djangoExcludeApps, setDjangoExcludeApps] = useState(
    "auth.permission,contenttypes,admin.logentry,sessions",
  );
  const [djangoOutput, setDjangoOutput] = useState("");
  const [dbbackupMode, setDbbackupMode] = useState<"backup" | "list" | "restore">("backup");
  const [dbbackupInputFilename, setDbbackupInputFilename] = useState("");
  const [dbbackupConfirm, setDbbackupConfirm] = useState("");
  const [dbbackupOutput, setDbbackupOutput] = useState("");
  const [commandCatalog, setCommandCatalog] = useState<Record<string, string>>({});

  const selectedBackupItem = useMemo(
    () => backups.find((item) => item.path === selectedBackup) || null,
    [backups, selectedBackup],
  );

  const loadBackups = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const payload = await listPortalDatabaseBackupsAdmin(50);
      setBackups(payload.results || []);
      if (!selectedBackup && payload.results.length > 0) {
        setSelectedBackup(payload.results[0].path);
      }
    } catch (loadError) {
      setError(resolveErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }, [selectedBackup]);

  async function loadTunnelStatus(): Promise<void> {
    try {
      const result = await managePortalDatabaseTunnelAdmin("status");
      setTunnelState(result.tunnel);
      setTunnelBindHost(result.tunnel.local_bind_host);
      setTunnelLocalPort(String(result.tunnel.local_port));
      setTunnelRemoteHost(result.tunnel.remote_db_host);
      setTunnelRemotePort(String(result.tunnel.remote_db_port));
    } catch (statusError) {
      setError(resolveErrorMessage(statusError));
    }
  }

  async function loadCommandCatalog(sampleBackupFile?: string): Promise<void> {
    try {
      const result = await fetchPortalDatabaseCommandCatalogAdmin(sampleBackupFile);
      setCommandCatalog(result.commands || {});
    } catch (catalogError) {
      setError(resolveErrorMessage(catalogError));
    }
  }

  useEffect(() => {
    void loadBackups();
    void loadTunnelStatus();
    void loadCommandCatalog();
  }, [loadBackups]);

  useEffect(() => {
    if (selectedBackup) {
      void loadCommandCatalog(selectedBackup);
    }
  }, [selectedBackup]);

  async function handleCreateBackup(): Promise<void> {
    setCreating(true);
    setError(null);
    setFeedback(null);
    try {
      const result = await createPortalDatabaseBackupAdmin({ label });
      setFeedback(`Backup criado: ${result.backup_file}`);
      await loadBackups();
    } catch (createError) {
      setError(resolveErrorMessage(createError));
    } finally {
      setCreating(false);
    }
  }

  async function handleRestoreBackup(): Promise<void> {
    if (!selectedBackup) {
      setError("Selecione um backup para restaurar.");
      return;
    }
    setRestoring(true);
    setError(null);
    setFeedback(null);
    try {
      const result = await restorePortalDatabaseBackupAdmin({
        backup_file: selectedBackup,
        confirm: confirmRestore,
      });
      setFeedback(result.summary);
    } catch (restoreError) {
      setError(resolveErrorMessage(restoreError));
    } finally {
      setRestoring(false);
    }
  }

  async function handleSyncToDev(): Promise<void> {
    if (!selectedBackup) {
      setError("Selecione um backup para sincronizar.");
      return;
    }
    setSyncing(true);
    setError(null);
    setFeedback(null);
    try {
      const result = await syncPortalDatabaseToDevAdmin({ backup_file: selectedBackup });
      setFeedback(result.summary);
    } catch (syncError) {
      setError(resolveErrorMessage(syncError));
    } finally {
      setSyncing(false);
    }
  }

  async function handleCopyBackupViaScp(): Promise<void> {
    if (!selectedBackup) {
      setError("Selecione um backup para copiar via SCP.");
      return;
    }
    setScpCopying(true);
    setError(null);
    setFeedback(null);
    try {
      const result = await copyPortalDatabaseBackupToDevViaScpAdmin({
        backup_file: selectedBackup,
      });
      setFeedback(`Backup copiado via SCP: ${result.local_dump_file}`);
    } catch (copyError) {
      setError(resolveErrorMessage(copyError));
    } finally {
      setScpCopying(false);
    }
  }

  async function handleSaveTunnelConfig(): Promise<void> {
    setTunnelBusy(true);
    setError(null);
    setFeedback(null);
    try {
      await savePortalDatabaseTunnelAdmin({
        local_bind_host: tunnelBindHost,
        local_port: Number(tunnelLocalPort || "55432"),
        remote_db_host: tunnelRemoteHost,
        remote_db_port: Number(tunnelRemotePort || "5432"),
      });
      setFeedback("Configuracao de tunnel salva.");
      await loadTunnelStatus();
    } catch (saveError) {
      setError(resolveErrorMessage(saveError));
    } finally {
      setTunnelBusy(false);
    }
  }

  async function handleTunnelAction(action: "start" | "stop" | "status"): Promise<void> {
    setTunnelBusy(true);
    setError(null);
    setFeedback(null);
    try {
      const result = await managePortalDatabaseTunnelAdmin(action);
      setTunnelState(result.tunnel);
      setFeedback(`Tunnel: acao ${action} executada.`);
    } catch (actionError) {
      setError(resolveErrorMessage(actionError));
    } finally {
      setTunnelBusy(false);
    }
  }

  async function handleRunPsql(): Promise<void> {
    setPsqlBusy(true);
    setError(null);
    setFeedback(null);
    setPsqlOutput("");
    try {
      const result = await executePortalDatabasePsqlAdmin({
        command: psqlCommand,
        read_only: psqlReadOnly,
        confirm: psqlConfirm,
      });
      setPsqlOutput([result.stdout, result.stderr].filter(Boolean).join("\n"));
      if (result.ok) {
        setFeedback("Comando psql executado com sucesso.");
      } else {
        setError("Comando psql finalizou com erro.");
      }
    } catch (runError) {
      setError(resolveErrorMessage(runError));
    } finally {
      setPsqlBusy(false);
    }
  }

  async function handleDjangoSync(mode: "dump" | "sync_dev"): Promise<void> {
    setDjangoBusy(true);
    setError(null);
    setFeedback(null);
    setDjangoOutput("");
    try {
      const excludeApps = djangoExcludeApps
        .split(",")
        .map((item) => item.trim())
        .filter((item) => item.length > 0);
      const result = await syncPortalDatabaseViaDjangoAdmin({ mode, exclude_apps: excludeApps });
      setDjangoOutput(
        `Arquivo: ${result.local_dump_file}\nModo: ${result.mode}\nSynced: ${String(result.synced)}`,
      );
      setFeedback(
        mode === "sync_dev"
          ? "Sincronizacao Django para DEV concluida."
          : "Dump Django remoto concluido.",
      );
    } catch (syncError) {
      setError(resolveErrorMessage(syncError));
    } finally {
      setDjangoBusy(false);
    }
  }

  async function handleDjangoDbbackup(): Promise<void> {
    setDbbackupBusy(true);
    setError(null);
    setFeedback(null);
    setDbbackupOutput("");
    try {
      const payload: {
        mode: "backup" | "list" | "restore";
        input_filename?: string;
        confirm?: string;
      } = { mode: dbbackupMode };
      if (dbbackupMode === "restore") {
        payload.input_filename = dbbackupInputFilename;
        payload.confirm = dbbackupConfirm;
      }
      const result = await runPortalDatabaseDjangoDbbackupAdmin(payload);
      setDbbackupOutput([result.stdout, result.stderr].filter(Boolean).join("\n"));
      if (result.ok) {
        setFeedback(`django-dbbackup (${result.mode}) executado com sucesso.`);
      } else {
        setError(`django-dbbackup (${result.mode}) finalizou com erro.`);
      }
    } catch (dbbackupError) {
      setError(resolveErrorMessage(dbbackupError));
    } finally {
      setDbbackupBusy(false);
    }
  }

  async function handleCopyCommandToClipboard(command: string): Promise<void> {
    if (!command.trim()) {
      return;
    }
    try {
      await navigator.clipboard.writeText(command);
      setFeedback("Comando copiado para a area de transferencia.");
    } catch {
      setError("Nao foi possivel copiar comando automaticamente.");
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-text">Banco de dados: operacao completa</h3>
          <p className="mt-1 text-xs text-muted">
            1) Tunnel SSH, 2) comandos psql via SSH, 3) sync Django (dumpdata/loaddata).
          </p>
        </div>
        <StatusPill tone="info">PostgreSQL + Django</StatusPill>
      </div>

      <div className="mt-4 grid gap-2 md:grid-cols-5">
        {[
          ["tunnel", "1. Tunnel SSH"],
          ["psql", "2. psql remoto"],
          ["backup", "3. Backups"],
          ["django", "4. Django libs"],
          ["commands", "5. Comandos"],
        ].map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => setActiveStep(key as typeof activeStep)}
            className={[
              "rounded-md border px-3 py-2 text-xs font-semibold transition",
              activeStep === key
                ? "border-primary bg-primary/10 text-primary"
                : "border-border bg-bg text-text hover:border-primary",
            ].join(" ")}
          >
            {label}
          </button>
        ))}
      </div>

      {activeStep === "tunnel" && (
        <article className="mt-4 rounded-xl border border-border bg-bg p-4">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <h4 className="text-sm font-semibold text-text">Tunnel SSH para banco remoto</h4>
            <StatusPill tone={tunnelState.status === "active" ? "success" : "neutral"}>
              {tunnelState.status === "active" ? "Ativo" : "Inativo"}
            </StatusPill>
          </div>
          <div className="mt-3 grid gap-3 md:grid-cols-4">
            <label className="grid gap-1 text-xs text-muted">
              Bind local
              <input
                value={tunnelBindHost}
                onChange={(event) => setTunnelBindHost(event.currentTarget.value)}
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-xs text-muted">
              Porta local
              <input
                value={tunnelLocalPort}
                onChange={(event) => setTunnelLocalPort(event.currentTarget.value)}
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-xs text-muted">
              Host DB remoto
              <input
                value={tunnelRemoteHost}
                onChange={(event) => setTunnelRemoteHost(event.currentTarget.value)}
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
              />
            </label>
            <label className="grid gap-1 text-xs text-muted">
              Porta DB remota
              <input
                value={tunnelRemotePort}
                onChange={(event) => setTunnelRemotePort(event.currentTarget.value)}
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
              />
            </label>
          </div>
          <p className="mt-2 text-xs text-muted">
            PID: <strong className="text-text">{tunnelState.pid || "-"}</strong> · Start:{" "}
            <strong className="text-text">{formatDate(tunnelState.last_started_at)}</strong> ·
            Stop: <strong className="text-text">{formatDate(tunnelState.last_stopped_at)}</strong>
          </p>
          <div className="mt-3 flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleSaveTunnelConfig()}
              disabled={tunnelBusy}
              className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:opacity-60"
            >
              Salvar tunnel
            </button>
            <button
              type="button"
              onClick={() => void handleTunnelAction("status")}
              disabled={tunnelBusy}
              className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:opacity-60"
            >
              Status
            </button>
            <button
              type="button"
              onClick={() => void handleTunnelAction("start")}
              disabled={tunnelBusy}
              className="rounded-md border border-emerald-400 bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 transition hover:bg-emerald-100 disabled:opacity-60"
            >
              Ativar tunnel
            </button>
            <button
              type="button"
              onClick={() => void handleTunnelAction("stop")}
              disabled={tunnelBusy}
              className="rounded-md border border-rose-400 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:opacity-60"
            >
              Desativar tunnel
            </button>
          </div>
        </article>
      )}

      {activeStep === "psql" && (
        <article className="mt-4 rounded-xl border border-border bg-bg p-4">
          <h4 className="text-sm font-semibold text-text">Comandos psql via SSH</h4>
          <p className="mt-1 text-xs text-muted">
            Modo seguro: read-only habilitado restringe para SELECT/SHOW/EXPLAIN/WITH.
          </p>
          <div className="mt-3 grid gap-3">
            <label className="grid gap-1 text-xs text-muted">
              SQL
              <textarea
                rows={5}
                value={psqlCommand}
                onChange={(event) => setPsqlCommand(event.currentTarget.value)}
                className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
              />
            </label>
            <div className="flex flex-wrap items-center gap-4">
              <label className="inline-flex items-center gap-2 text-xs text-text">
                <input
                  type="checkbox"
                  checked={psqlReadOnly}
                  onChange={(event) => setPsqlReadOnly(event.currentTarget.checked)}
                  className="h-4 w-4 border-border text-primary"
                />
                Executar em modo read-only
              </label>
              {!psqlReadOnly && (
                <label className="grid gap-1 text-xs text-muted">
                  Confirmacao (EXECUTAR)
                  <input
                    value={psqlConfirm}
                    onChange={(event) => setPsqlConfirm(event.currentTarget.value)}
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    placeholder="EXECUTAR"
                  />
                </label>
              )}
            </div>
            <button
              type="button"
              onClick={() => void handleRunPsql()}
              disabled={psqlBusy}
              className="w-fit rounded-md border border-border px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:opacity-60"
            >
              {psqlBusy ? "Executando..." : "Executar psql"}
            </button>
            {psqlOutput && (
              <pre className="max-h-56 overflow-auto rounded-md border border-border bg-surface/70 p-2 text-xs text-text">
                {psqlOutput}
              </pre>
            )}
          </div>
        </article>
      )}

      {activeStep === "backup" && (
        <article className="mt-4 rounded-xl border border-border bg-bg p-4">
          <h4 className="text-sm font-semibold text-text">
            Backup/restore por dump PostgreSQL
          </h4>
        <div className="mt-3 grid gap-3 md:grid-cols-[1fr_auto]">
          <label className="grid gap-1 text-sm text-muted">
            Label do backup (ex.: pre-release, hotfix, manual)
            <input
              value={label}
              onChange={(event) => setLabel(event.currentTarget.value)}
              className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
              placeholder="manual"
            />
          </label>
          <div className="flex items-end">
            <button
              type="button"
              onClick={() => void handleCreateBackup()}
              disabled={creating || restoring || syncing}
              className="w-full rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60 md:w-auto"
            >
              {creating ? "Gerando backup..." : "Criar backup remoto"}
            </button>
          </div>
        </div>

        <div className="mt-4 rounded-xl border border-border bg-surface/60 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <p className="text-sm font-semibold text-text">Backups disponiveis</p>
            <button
              type="button"
              onClick={() => void loadBackups()}
              disabled={loading}
              className="rounded-md border border-border px-3 py-1 text-xs font-semibold text-text transition hover:border-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {loading ? "Atualizando..." : "Atualizar lista"}
            </button>
          </div>

          <div className="mt-3 grid gap-2">
            {backups.map((item) => (
              <label
                key={item.path}
                className="flex cursor-pointer items-center justify-between gap-2 rounded-md border border-border px-3 py-2 text-xs text-text"
              >
                <span className="inline-flex items-center gap-2">
                  <input
                    type="radio"
                    name="db-backup"
                    checked={selectedBackup === item.path}
                    onChange={() => setSelectedBackup(item.path)}
                    className="h-4 w-4 border-border text-primary"
                  />
                  <span>{item.filename}</span>
                </span>
                <span className="text-muted">
                  {formatBytes(item.size_bytes)} · {formatDate(item.updated_at)}
                </span>
              </label>
            ))}
            {!loading && backups.length === 0 && (
              <p className="rounded-md border border-border bg-bg px-3 py-2 text-xs text-muted">
                Nenhum backup remoto encontrado.
              </p>
            )}
          </div>
        </div>

        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <article className="rounded-xl border border-border bg-surface/60 p-4">
            <h4 className="text-sm font-semibold text-text">Restaurar producao</h4>
            <p className="mt-1 text-xs text-muted">
              Acao critica. Digite <code>RESTAURAR</code> para confirmar.
            </p>
            <label className="mt-3 grid gap-1 text-xs text-muted">
              Confirmacao
              <input
                value={confirmRestore}
                onChange={(event) => setConfirmRestore(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                placeholder="RESTAURAR"
              />
            </label>
            <button
              type="button"
              onClick={() => void handleRestoreBackup()}
              disabled={!selectedBackup || restoring || creating || syncing}
              className="mt-3 rounded-md border border-rose-400 bg-rose-50 px-4 py-2 text-sm font-semibold text-rose-700 transition hover:bg-rose-100 disabled:cursor-not-allowed disabled:opacity-60"
            >
              {restoring ? "Restaurando..." : "Restaurar backup em producao"}
            </button>
          </article>

          <article className="rounded-xl border border-border bg-surface/60 p-4">
            <h4 className="text-sm font-semibold text-text">Sincronizar para DEV</h4>
            <p className="mt-1 text-xs text-muted">
              Transfere o backup selecionado e restaura no banco local DEV.
            </p>
            <p className="mt-2 rounded-md border border-border bg-bg px-3 py-2 text-xs text-muted">
              Backup selecionado:{" "}
              <strong className="text-text">{selectedBackupItem?.filename || "-"}</strong>
            </p>
            <div className="mt-3 flex flex-wrap gap-2">
              <button
                type="button"
                onClick={() => void handleSyncToDev()}
                disabled={!selectedBackup || syncing || creating || restoring}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {syncing ? "Sincronizando..." : "Sincronizar backup para DEV"}
              </button>
              <button
                type="button"
                onClick={() => void handleCopyBackupViaScp()}
                disabled={!selectedBackup || scpCopying || creating || restoring}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:cursor-not-allowed disabled:opacity-60"
              >
                {scpCopying ? "Copiando..." : "Copiar backup via SCP"}
              </button>
            </div>
          </article>
        </div>
        </article>
      )}

      {activeStep === "django" && (
        <article className="mt-4 rounded-xl border border-border bg-bg p-4">
          <h4 className="text-sm font-semibold text-text">Bibliotecas Django (sincronizado)</h4>
          <p className="mt-1 text-xs text-muted">
            `dumpdata/loaddata` e `django-dbbackup/dbrestore` para operacao de alto nivel.
          </p>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div className="rounded-md border border-border bg-surface/60 p-3">
              <p className="text-xs font-semibold text-text">Django dumpdata/loaddata</p>
              <label className="mt-2 grid gap-1 text-xs text-muted">
                Excluir apps/modelos (CSV)
                <input
                  value={djangoExcludeApps}
                  onChange={(event) => setDjangoExcludeApps(event.currentTarget.value)}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                  placeholder="auth.permission,contenttypes,admin.logentry,sessions"
                />
              </label>
              <div className="mt-2 flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void handleDjangoSync("dump")}
                  disabled={djangoBusy}
                  className="rounded-md border border-border px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:opacity-60"
                >
                  {djangoBusy ? "Processando..." : "Gerar dump remoto"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleDjangoSync("sync_dev")}
                  disabled={djangoBusy}
                  className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:opacity-60"
                >
                  {djangoBusy ? "Processando..." : "Aplicar no DEV"}
                </button>
              </div>
              {djangoOutput && (
                <pre className="mt-2 max-h-40 overflow-auto rounded-md border border-border bg-bg p-2 text-xs text-text">
                  {djangoOutput}
                </pre>
              )}
            </div>

            <div className="rounded-md border border-border bg-surface/60 p-3">
              <p className="text-xs font-semibold text-text">django-dbbackup/dbrestore</p>
              <label className="mt-2 grid gap-1 text-xs text-muted">
                Modo
                <select
                  value={dbbackupMode}
                  onChange={(event) =>
                    setDbbackupMode(
                      event.currentTarget.value as "backup" | "list" | "restore",
                    )
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="backup">dbbackup</option>
                  <option value="list">listbackups</option>
                  <option value="restore">dbrestore</option>
                </select>
              </label>
              {dbbackupMode === "restore" && (
                <div className="mt-2 grid gap-2">
                  <label className="grid gap-1 text-xs text-muted">
                    input_filename (remoto)
                    <input
                      value={dbbackupInputFilename}
                      onChange={(event) => setDbbackupInputFilename(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="/home/ubuntu/mrquentinha/.runtime/dbbackup/..."
                    />
                  </label>
                  <label className="grid gap-1 text-xs text-muted">
                    Confirmacao (RESTAURAR)
                    <input
                      value={dbbackupConfirm}
                      onChange={(event) => setDbbackupConfirm(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="RESTAURAR"
                    />
                  </label>
                </div>
              )}
              <button
                type="button"
                onClick={() => void handleDjangoDbbackup()}
                disabled={dbbackupBusy}
                className="mt-2 rounded-md border border-border px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:opacity-60"
              >
                {dbbackupBusy ? "Executando..." : "Executar django-dbbackup"}
              </button>
              {dbbackupOutput && (
                <pre className="mt-2 max-h-40 overflow-auto rounded-md border border-border bg-bg p-2 text-xs text-text">
                  {dbbackupOutput}
                </pre>
              )}
            </div>
          </div>
        </article>
      )}

      {activeStep === "commands" && (
        <article className="mt-4 rounded-xl border border-border bg-bg p-4">
          <h4 className="text-sm font-semibold text-text">Comandos e scripts prontos</h4>
          <p className="mt-1 text-xs text-muted">
            Comandos operacionais gerados com base na configuracao SSH atual (mascarados).
          </p>
          <div className="mt-3 grid gap-3">
            {Object.entries(commandCatalog).map(([key, command]) => (
              <div key={key} className="rounded-md border border-border bg-surface/60 p-3">
                <div className="flex items-center justify-between gap-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.06em] text-text">
                    {key.replaceAll("_", " ")}
                  </p>
                  <button
                    type="button"
                    onClick={() => void handleCopyCommandToClipboard(command)}
                    className="rounded-md border border-border px-2 py-1 text-xs font-semibold text-text transition hover:border-primary"
                  >
                    Copiar
                  </button>
                </div>
                <pre className="mt-2 overflow-auto rounded-md border border-border bg-bg p-2 text-xs text-text">
                  {command}
                </pre>
              </div>
            ))}
          </div>
        </article>
      )}

      {error && (
        <p className="mt-4 rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}
      {feedback && (
        <p className="mt-4 rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          {feedback}
        </p>
      )}
    </section>
  );
}

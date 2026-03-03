"use client";

import { useEffect, useMemo, useState, type ChangeEvent } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  ensurePortalConfigAdmin,
  probePortalDatabaseSshAdmin,
  savePortalDatabaseSshAdmin,
  uploadPortalDatabaseSshKeyAdmin,
} from "@/lib/api";
import { useAdminSession } from "@/components/AdminSessionGate";
import type { PortalConfigData, PortalInstallerSshConfig } from "@/types/api";

type DatabaseSshAccessPanelProps = {
  compact?: boolean;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada na operacao SSH.";
}

function extractSshSettings(config: PortalConfigData | null): PortalInstallerSshConfig {
  const draft = config?.installer_settings?.wizard?.draft;
  const ssh = draft?.ssh;
  return {
    host: ssh?.host || "",
    port: Number(ssh?.port || 22),
    user: ssh?.user || "",
    auth_mode: ssh?.auth_mode === "password" ? "password" : "key",
    key_path: ssh?.key_path || "",
    password: ssh?.password || "",
    repo_path: ssh?.repo_path || "$HOME/mrquentinha",
    auto_clone_repo: Boolean(ssh?.auto_clone_repo),
    git_remote_url: ssh?.git_remote_url || "",
    git_branch: ssh?.git_branch || "main",
  };
}

function isDevOrHybrid(config: PortalConfigData | null): boolean {
  if (!config) {
    return false;
  }
  const mode = String(config?.installer_settings?.wizard?.draft?.mode || "").toLowerCase();
  const cloudflareMode = String(config?.cloudflare_settings?.mode || "").toLowerCase();
  const rootDomain = String(config?.root_domain || "").toLowerCase();
  return mode === "dev" || cloudflareMode === "hybrid" || rootDomain.endsWith(".local");
}

export function DatabaseSshAccessPanel({ compact = false }: DatabaseSshAccessPanelProps) {
  const { user } = useAdminSession();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [probing, setProbing] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const [config, setConfig] = useState<PortalConfigData | null>(null);
  const [host, setHost] = useState("");
  const [port, setPort] = useState("22");
  const [sshUser, setSshUser] = useState("");
  const [authMode, setAuthMode] = useState<"key" | "password">("key");
  const [keyPath, setKeyPath] = useState("");
  const [password, setPassword] = useState("");
  const [repoPath, setRepoPath] = useState("$HOME/mrquentinha");

  const isAdmin = useMemo(() => {
    if (!user) {
      return false;
    }
    if ((user as { is_superuser?: boolean }).is_superuser) {
      return true;
    }
    return (user.roles || []).map((role) => role.toUpperCase()).includes("ADMIN");
  }, [user]);

  async function load(): Promise<void> {
    setLoading(true);
    setError(null);
    try {
      const payload = await ensurePortalConfigAdmin();
      setConfig(payload);
      const ssh = extractSshSettings(payload);
      setHost(ssh.host);
      setPort(String(ssh.port || 22));
      setSshUser(ssh.user);
      setAuthMode(ssh.auth_mode);
      setKeyPath(ssh.key_path);
      setPassword(ssh.password);
      setRepoPath(ssh.repo_path || "$HOME/mrquentinha");
    } catch (loadError) {
      setError(resolveErrorMessage(loadError));
    } finally {
      setLoading(false);
    }
  }

  useEffect(() => {
    void load();
  }, []);

  async function handleSave(): Promise<void> {
    setSaving(true);
    setError(null);
    setFeedback(null);
    try {
      const payload = await savePortalDatabaseSshAdmin({
        host,
        port: Number(port || "22"),
        user: sshUser,
        auth_mode: authMode,
        key_path: keyPath,
        password,
        repo_path: repoPath || "$HOME/mrquentinha",
      });
      setConfig(payload);
      setFeedback("Configuracao SSH salva com sucesso.");
    } catch (saveError) {
      setError(resolveErrorMessage(saveError));
    } finally {
      setSaving(false);
    }
  }

  async function handleProbe(): Promise<void> {
    setProbing(true);
    setError(null);
    setFeedback(null);
    try {
      const result = await probePortalDatabaseSshAdmin({
        host,
        port: Number(port || "22"),
        user: sshUser,
        auth_mode: authMode,
        key_path: keyPath,
        password,
        repo_path: repoPath || "$HOME/mrquentinha",
      });
      setFeedback(String(result?.check?.detail || "Conectividade SSH validada."));
    } catch (probeError) {
      setError(resolveErrorMessage(probeError));
    } finally {
      setProbing(false);
    }
  }

  async function handlePemUpload(event: ChangeEvent<HTMLInputElement>): Promise<void> {
    const file = event.currentTarget.files?.[0];
    if (!file) {
      return;
    }
    setUploading(true);
    setError(null);
    setFeedback(null);
    try {
      const content = await file.text();
      const result = await uploadPortalDatabaseSshKeyAdmin({
        filename: file.name,
        content,
      });
      setKeyPath(result.key_path);
      setFeedback(`Chave .pem salva com sucesso em ${result.key_path}.`);
    } catch (uploadError) {
      setError(resolveErrorMessage(uploadError));
    } finally {
      setUploading(false);
      event.currentTarget.value = "";
    }
  }

  if (!isAdmin) {
    return (
      <section className="rounded-2xl border border-amber-300 bg-amber-50 p-4 text-amber-900">
        <h3 className="text-base font-semibold">Acesso restrito</h3>
        <p className="mt-1 text-sm">
          Esta area e exclusiva para administradores (perfil ADMIN/superuser).
        </p>
      </section>
    );
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-border bg-surface/70 p-4">
        <p className="text-sm text-muted">Carregando configuracao SSH...</p>
      </section>
    );
  }

  const envAllowed = isDevOrHybrid(config);

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-5 shadow-sm">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 className="text-base font-semibold text-text">SSH producao (pre-requisito)</h3>
          <p className="mt-1 text-xs text-muted">
            Configure host/usuario/chave para habilitar backup, restore e sincronizacao de dados.
          </p>
        </div>
        <StatusPill tone={envAllowed ? "success" : "warning"}>
          {envAllowed ? "Permitido (dev/hibrido)" : "Bloqueado fora de dev/hibrido"}
        </StatusPill>
      </div>

      {!envAllowed && (
        <p className="mt-3 rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-xs text-amber-900">
          Para alterar esta configuracao, ajuste o ambiente para modo DEV ou HYBRID.
        </p>
      )}

      <div className="mt-4 grid gap-3 md:grid-cols-2 lg:grid-cols-4">
        <label className="grid gap-1 text-sm text-muted">
          Host SSH
          <input
            value={host}
            onChange={(event) => setHost(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="44.192.27.104"
            disabled={!envAllowed}
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Porta SSH
          <input
            value={port}
            onChange={(event) => setPort(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="22"
            disabled={!envAllowed}
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Usuario SSH
          <input
            value={sshUser}
            onChange={(event) => setSshUser(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="ubuntu"
            disabled={!envAllowed}
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Autenticacao
          <select
            value={authMode}
            onChange={(event) => setAuthMode(event.currentTarget.value as "key" | "password")}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            disabled={!envAllowed}
          >
            <option value="key">Chave .pem</option>
            <option value="password">Senha</option>
          </select>
        </label>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <label className="grid gap-1 text-sm text-muted">
          Caminho da chave .pem
          <input
            value={keyPath}
            onChange={(event) => setKeyPath(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="/home/roberto/.ssh/minha-chave.pem"
            disabled={!envAllowed}
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Upload da chave .pem
          <input
            type="file"
            accept=".pem"
            onChange={(event) => void handlePemUpload(event)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text file:mr-3 file:rounded-md file:border-0 file:bg-primary file:px-3 file:py-1 file:text-xs file:font-semibold file:text-white"
            disabled={!envAllowed || uploading}
          />
        </label>
      </div>

      <div className="mt-3 grid gap-3 md:grid-cols-2">
        <label className="grid gap-1 text-sm text-muted">
          Senha SSH (opcional/chave complementar)
          <input
            type="password"
            value={password}
            onChange={(event) => setPassword(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="********"
            disabled={!envAllowed}
          />
        </label>
        <label className="grid gap-1 text-sm text-muted">
          Caminho do repositorio remoto
          <input
            value={repoPath}
            onChange={(event) => setRepoPath(event.currentTarget.value)}
            className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
            placeholder="$HOME/mrquentinha"
            disabled={!envAllowed}
          />
        </label>
      </div>

      {error && (
        <p className="mt-3 rounded-md border border-rose-300 bg-rose-50 px-3 py-2 text-xs text-rose-700">
          {error}
        </p>
      )}
      {feedback && (
        <p className="mt-3 rounded-md border border-emerald-300 bg-emerald-50 px-3 py-2 text-xs text-emerald-700">
          {feedback}
        </p>
      )}

      <div className="mt-4 flex flex-wrap justify-end gap-2">
        <button
          type="button"
          onClick={() => void handleProbe()}
          disabled={!envAllowed || probing || saving}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary disabled:cursor-not-allowed disabled:opacity-60"
        >
          {probing ? "Validando..." : "Validar conectividade SSH"}
        </button>
        <button
          type="button"
          onClick={() => void handleSave()}
          disabled={!envAllowed || saving || probing}
          className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
        >
          {saving ? "Salvando..." : "Salvar acesso SSH"}
        </button>
      </div>

      {!compact && (
        <p className="mt-3 text-xs text-muted">
          Seguranca: credenciais sensiveis nao sao exibidas em logs de comando. Use esta area
          apenas em ambiente controlado e com perfis admin.
        </p>
      )}
    </section>
  );
}

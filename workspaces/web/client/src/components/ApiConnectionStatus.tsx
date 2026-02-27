"use client";

import { useEffect, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { getResolvedApiBaseUrl } from "@/lib/api";
import { trackNetworkRequest } from "@/lib/networkPreloader";

type ApiHealthState = "checking" | "ok" | "error";

function resolveTone(state: ApiHealthState): "success" | "warning" | "danger" {
  if (state === "ok") {
    return "success";
  }

  if (state === "error") {
    return "danger";
  }

  return "warning";
}

function resolveLabel(state: ApiHealthState): string {
  if (state === "ok") {
    return "API online";
  }

  if (state === "error") {
    return "API indisponivel";
  }

  return "Verificando API";
}

export function ApiConnectionStatus() {
  const [state, setState] = useState<ApiHealthState>("checking");
  const [message, setMessage] = useState<string>("");
  const [apiBaseUrl, setApiBaseUrl] = useState<string>(() => getResolvedApiBaseUrl());

  useEffect(() => {
    let mounted = true;

    async function loadRuntimeApiBaseUrl() {
      try {
        const response = await fetch("/api/runtime/config", {
          cache: "no-store",
        });
        if (!response.ok) {
          return;
        }

        const payload = (await response.json()) as { api_base_url?: unknown };
        const runtimeApiBaseUrl = String(payload.api_base_url ?? "").trim().replace(/\/$/, "");
        if (mounted && runtimeApiBaseUrl) {
          setApiBaseUrl(runtimeApiBaseUrl);
        }
      } catch {
        // Mantem fallback local quando runtime nao responder.
      }
    }

    void loadRuntimeApiBaseUrl();
    return () => {
      mounted = false;
    };
  }, []);
  
  useEffect(() => {
    let mounted = true;

    async function checkHealth() {
      if (!apiBaseUrl) {
        if (mounted) {
          setState("error");
          setMessage("Base da API nao configurada.");
        }
        return;
      }

      setState("checking");
      setMessage("");

      try {
        const response = await trackNetworkRequest(() =>
          fetch(`${apiBaseUrl}/api/v1/health`, {
            cache: "no-store",
          }),
        );

        if (!mounted) {
          return;
        }

        if (!response.ok) {
          setState("error");
          setMessage(`Health check retornou HTTP ${response.status}.`);
          return;
        }

        setState("ok");
      } catch {
        if (!mounted) {
          return;
        }
        setState("error");
        setMessage("Nao foi possivel conectar no backend.");
      }
    }

    void checkHealth();

    return () => {
      mounted = false;
    };
  }, [apiBaseUrl]);

  return (
    <div className="rounded-xl border border-border bg-bg/80 px-3 py-2 text-xs text-muted">
      <div className="flex flex-wrap items-center gap-2">
        <span className="font-semibold uppercase tracking-[0.1em] text-text">API</span>
        <StatusPill tone={resolveTone(state)}>{resolveLabel(state)}</StatusPill>
        <span className="truncate">Base: {apiBaseUrl || "nao definida"}</span>
      </div>
      {message && <p className="mt-1 text-[11px] text-red-600 dark:text-red-300">{message}</p>}
    </div>
  );
}

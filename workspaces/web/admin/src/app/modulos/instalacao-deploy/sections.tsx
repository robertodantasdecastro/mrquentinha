"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import { InstallAssistantPanel } from "@/components/modules/InstallAssistantPanel";
import { ApiError, ensurePortalConfigAdmin } from "@/lib/api";
import type { PortalConfigData } from "@/types/api";

export const INSTALL_DEPLOY_BASE_PATH = "/modulos/instalacao-deploy";

export const INSTALL_DEPLOY_MENU_ITEMS = [
  { key: "all", label: "Todos", href: INSTALL_DEPLOY_BASE_PATH },
  {
    key: "pre-requisitos",
    label: "Pre-requisitos",
    href: `${INSTALL_DEPLOY_BASE_PATH}/pre-requisitos#pre-requisitos`,
  },
  {
    key: "assistente",
    label: "Assistente",
    href: `${INSTALL_DEPLOY_BASE_PATH}/assistente#assistente-instalacao`,
  },
];

export type InstallDeploySectionKey = "all" | "pre-requisitos" | "assistente";

type InstallDeploySectionsProps = {
  activeSection?: InstallDeploySectionKey;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha ao carregar configuracoes do assistente de instalacao/deploy.";
}

export function InstallDeploySections({ activeSection = "all" }: InstallDeploySectionsProps) {
  const [config, setConfig] = useState<PortalConfigData | null>(null);
  const [loading, setLoading] = useState(true);
  const [errorMessage, setErrorMessage] = useState("");

  useEffect(() => {
    let mounted = true;

    async function loadConfig() {
      setLoading(true);
      setErrorMessage("");
      try {
        const payload = await ensurePortalConfigAdmin();
        if (mounted) {
          setConfig(payload);
        }
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

    void loadConfig();

    return () => {
      mounted = false;
    };
  }, []);

  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "pre-requisitos") && (
        <section
          id="pre-requisitos"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Pre-requisitos de instalacao/deploy</h2>
              <p className="mt-1 text-sm text-muted">
                O modo producao exige dados de servidor/DNS e gateway de pagamento validos.
              </p>
            </div>
            <StatusPill tone="warning">Obrigatorio em producao</StatusPill>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-sm font-semibold text-text">Configuracoes de servidor e dominio</p>
              <p className="mt-1 text-xs text-muted">
                DNS/subdominios (portal, client, admin e API) sao usados pelo deploy automaticamente.
              </p>
              <Link
                href="/modulos/administracao-servidor/conectividade#conectividade"
                className="mt-3 inline-flex rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Abrir conectividade e dominio
              </Link>
            </article>

            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-sm font-semibold text-text">Gateway de pagamento</p>
              <p className="mt-1 text-xs text-muted">
                Configure provider por frontend (web e mobile), recebedor CPF/CNPJ e credenciais de API.
              </p>
              <Link
                href="/modulos/portal/pagamentos#pagamentos"
                className="mt-3 inline-flex rounded-md border border-border bg-surface px-3 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Abrir pagamentos
              </Link>
            </article>
          </div>
        </section>
      )}

      {(showAll || activeSection === "assistente") && (
        <section id="assistente" className="scroll-mt-24">
          {loading && <InlinePreloader message="Carregando assistente de instalacao/deploy..." />}
          {errorMessage && (
            <p className="rounded-md border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-700">
              {errorMessage}
            </p>
          )}
          {!loading && !errorMessage && (
            <InstallAssistantPanel
              config={config}
              onConfigUpdated={(nextConfig) => {
                setConfig(nextConfig);
              }}
            />
          )}
        </section>
      )}
    </>
  );
}

"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  ensurePortalConfigAdmin,
  publishPortalConfigAdmin,
  updatePortalConfigAdmin,
} from "@/lib/api";
import type {
  PortalConfigData,
  PortalTemplateData,
} from "@/types/api";

export const PORTAL_BASE_PATH = "/modulos/portal";

export const PORTAL_MENU_ITEMS = [
  { key: "all", label: "Todos", href: PORTAL_BASE_PATH },
  { key: "template", label: "Template ativo", href: `${PORTAL_BASE_PATH}/template#template` },
  { key: "publicacao", label: "Publicacao", href: `${PORTAL_BASE_PATH}/publicacao#publicacao` },
];

export type PortalSectionKey = "all" | "template" | "publicacao";

type PortalSectionsProps = {
  activeSection?: PortalSectionKey;
};

type TemplateOption = {
  id: string;
  label: string;
};

const TEMPLATE_LABEL_FALLBACK: Record<string, string> = {
  classic: "Classico",
  "letsfit-clean": "LetsFit Clean",
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada ao carregar configuracoes do portal.";
}

function normalizeTemplateOptions(
  availableTemplates: Array<PortalTemplateData | string>,
): TemplateOption[] {
  const templateMap = new Map<string, TemplateOption>();

  for (const item of availableTemplates) {
    if (typeof item === "string") {
      const templateId = item.trim();
      if (!templateId) {
        continue;
      }

      templateMap.set(templateId, {
        id: templateId,
        label: TEMPLATE_LABEL_FALLBACK[templateId] ?? templateId,
      });
      continue;
    }

    const templateId = item.id?.trim();
    if (!templateId) {
      continue;
    }

    templateMap.set(templateId, {
      id: templateId,
      label: item.label?.trim() || TEMPLATE_LABEL_FALLBACK[templateId] || templateId,
    });
  }

  return Array.from(templateMap.values());
}

function formatDateTime(value: string | null): string {
  if (!value) {
    return "Nao publicado";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

  return date.toLocaleString("pt-BR");
}

export function PortalSections({ activeSection = "all" }: PortalSectionsProps) {
  const [config, setConfig] = useState<PortalConfigData | null>(null);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const templateOptions = useMemo(() => {
    if (!config) {
      return [] as TemplateOption[];
    }

    return normalizeTemplateOptions(config.available_templates);
  }, [config]);

  useEffect(() => {
    let mounted = true;

    async function loadPortalConfig() {
      try {
        const configPayload = await ensurePortalConfigAdmin();
        if (!mounted) {
          return;
        }

        setConfig(configPayload);
        setSelectedTemplateId(configPayload.active_template);
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

    void loadPortalConfig();

    return () => {
      mounted = false;
    };
  }, []);

  const activeTemplateLabel = useMemo(() => {
    if (!config) {
      return "-";
    }

    return (
      templateOptions.find((option) => option.id === config.active_template)?.label ??
      TEMPLATE_LABEL_FALLBACK[config.active_template] ??
      config.active_template
    );
  }, [config, templateOptions]);

  const showAll = activeSection === "all";

  async function handleSaveTemplate() {
    if (!config || !selectedTemplateId) {
      return;
    }

    setSaving(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        active_template: selectedTemplateId,
      });
      setConfig(updatedConfig);
      setSelectedTemplateId(updatedConfig.active_template);
      setSuccessMessage("Template ativo atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handlePublishConfig() {
    setPublishing(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const publishedConfig = await publishPortalConfigAdmin();
      setConfig(publishedConfig);
      setSelectedTemplateId(publishedConfig.active_template);
      setSuccessMessage("Configuracao do portal publicada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setPublishing(false);
    }
  }

  return (
    <>
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div>
            <h2 className="text-lg font-semibold text-text">Resumo da configuracao</h2>
            <p className="mt-1 text-sm text-muted">
              Controle do template ativo e publicacao da configuracao do portal.
            </p>
          </div>
          {config?.is_published ? (
            <StatusPill tone="success">Publicado</StatusPill>
          ) : (
            <StatusPill tone="warning">Rascunho</StatusPill>
          )}
        </div>
        {loading && <p className="mt-3 text-sm text-muted">Carregando configuracoes do portal...</p>}
        {!loading && config && (
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template ativo</p>
              <p className="mt-1 text-base font-semibold text-text">{activeTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Templates disponiveis</p>
              <p className="mt-1 text-base font-semibold text-text">{templateOptions.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ultima publicacao</p>
              <p className="mt-1 text-base font-semibold text-text">{formatDateTime(config.published_at)}</p>
            </article>
          </div>
        )}
      </section>

      {(showAll || activeSection === "template") && (
        <section id="template" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Template ativo do portal</h2>
          <p className="mt-1 text-sm text-muted">
            Escolha entre os templates existentes no backend e salve o template principal.
          </p>
          <div className="mt-4 grid gap-3 md:max-w-xl">
            <label className="flex flex-col gap-2 text-sm font-medium text-text">
              Template
              <select
                value={selectedTemplateId}
                onChange={(event) => setSelectedTemplateId(event.target.value)}
                disabled={loading || saving || templateOptions.length === 0}
                className="rounded-xl border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                {templateOptions.length === 0 && (
                  <option value="">Nenhum template disponivel</option>
                )}
                {templateOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <div>
              <button
                type="button"
                onClick={() => void handleSaveTemplate()}
                disabled={
                  loading ||
                  saving ||
                  !config ||
                  !selectedTemplateId ||
                  selectedTemplateId === config.active_template
                }
                className="rounded-xl border border-primary bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:brightness-95 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {saving ? "Salvando..." : "Salvar template"}
              </button>
            </div>
          </div>
        </section>
      )}

      {(showAll || activeSection === "publicacao") && (
        <section id="publicacao" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <h2 className="text-lg font-semibold text-text">Publicacao</h2>
          <p className="mt-1 text-sm text-muted">
            Publica a configuracao atual para uso do portal publico.
          </p>
          <div className="mt-4">
            <button
              type="button"
              onClick={() => void handlePublishConfig()}
              disabled={loading || publishing || !config}
              className="rounded-xl border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {publishing ? "Publicando..." : "Publicar configuracao"}
            </button>
          </div>
        </section>
      )}

      {successMessage && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-700">
          {successMessage}
        </div>
      )}

      {errorMessage && (
        <div className="rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
          {errorMessage}
        </div>
      )}
    </>
  );
}

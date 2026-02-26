"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import {
  ApiError,
  ensurePortalConfigAdmin,
  listPortalSectionsAdmin,
  publishPortalConfigAdmin,
  updatePortalConfigAdmin,
  updatePortalSectionAdmin,
} from "@/lib/api";
import type {
  PortalConfigData,
  PortalSectionData,
  PortalTemplateData,
} from "@/types/api";

export const PORTAL_BASE_PATH = "/modulos/portal";

export const PORTAL_MENU_ITEMS = [
  { key: "all", label: "Todos", href: PORTAL_BASE_PATH },
  { key: "template", label: "Template ativo", href: `${PORTAL_BASE_PATH}/template#template` },
  { key: "conteudo", label: "Conteudo dinamico", href: `${PORTAL_BASE_PATH}/conteudo#conteudo` },
  { key: "publicacao", label: "Publicacao", href: `${PORTAL_BASE_PATH}/publicacao#publicacao` },
];

export type PortalSectionKey = "all" | "template" | "conteudo" | "publicacao";

type PortalSectionsProps = {
  activeSection?: PortalSectionKey;
};

type TemplateOption = {
  id: string;
  label: string;
};

type PortalPageOption = {
  value: string;
  label: string;
};

const TEMPLATE_LABEL_FALLBACK: Record<string, string> = {
  classic: "Classico",
  "letsfit-clean": "LetsFit Clean",
};

const PORTAL_PAGE_LABELS: Record<string, string> = {
  home: "Home",
  cardapio: "Cardapio",
  sobre: "Sobre",
  "como-funciona": "Como funciona",
  contato: "Contato",
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

function formatPortalPageLabel(page: string): string {
  return PORTAL_PAGE_LABELS[page] ?? page;
}

function stringifyBodyJson(value: unknown): string {
  try {
    return JSON.stringify(value ?? {}, null, 2);
  } catch {
    return "{}";
  }
}

function parseBodyJson(value: string): unknown {
  const normalized = value.trim();
  if (!normalized) {
    return {};
  }

  return JSON.parse(normalized) as unknown;
}

export function PortalSections({ activeSection = "all" }: PortalSectionsProps) {
  const [config, setConfig] = useState<PortalConfigData | null>(null);
  const [sections, setSections] = useState<PortalSectionData[]>([]);
  const [selectedTemplateId, setSelectedTemplateId] = useState("");
  const [contentTemplateId, setContentTemplateId] = useState("");
  const [contentPageFilter, setContentPageFilter] = useState("all");
  const [selectedSectionId, setSelectedSectionId] = useState("");
  const [sectionTitleDraft, setSectionTitleDraft] = useState("");
  const [sectionSortOrderDraft, setSectionSortOrderDraft] = useState("0");
  const [sectionEnabledDraft, setSectionEnabledDraft] = useState(true);
  const [sectionBodyJsonDraft, setSectionBodyJsonDraft] = useState("{}");

  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [savingSection, setSavingSection] = useState(false);
  const [publishing, setPublishing] = useState(false);
  const [refreshingSections, setRefreshingSections] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const templateOptions = useMemo(() => {
    if (!config) {
      return [] as TemplateOption[];
    }

    return normalizeTemplateOptions(config.available_templates);
  }, [config]);

  const pageOptions = useMemo<PortalPageOption[]>(() => {
    const values = new Set<string>();
    for (const section of sections) {
      values.add(section.page);
    }

    const sortedValues = Array.from(values).sort((left, right) =>
      formatPortalPageLabel(left).localeCompare(formatPortalPageLabel(right), "pt-BR"),
    );

    return [
      { value: "all", label: "Todas as paginas" },
      ...sortedValues.map((value) => ({
        value,
        label: formatPortalPageLabel(value),
      })),
    ];
  }, [sections]);

  const filteredSections = useMemo(() => {
    return sections
      .filter((section) => {
        const byTemplate = contentTemplateId ? section.template_id === contentTemplateId : true;
        const byPage = contentPageFilter === "all" ? true : section.page === contentPageFilter;
        return byTemplate && byPage;
      })
      .sort((left, right) => {
        if (left.sort_order !== right.sort_order) {
          return left.sort_order - right.sort_order;
        }
        return left.id - right.id;
      });
  }, [contentPageFilter, contentTemplateId, sections]);

  const selectedSection = useMemo(
    () =>
      filteredSections.find(
        (section) => String(section.id) === selectedSectionId,
      ) ?? null,
    [filteredSections, selectedSectionId],
  );

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

  useEffect(() => {
    let mounted = true;

    async function loadPortalData() {
      try {
        const [configPayload, sectionsPayload] = await Promise.all([
          ensurePortalConfigAdmin(),
          listPortalSectionsAdmin(),
        ]);
        if (!mounted) {
          return;
        }

        const normalizedTemplateOptions = normalizeTemplateOptions(
          configPayload.available_templates,
        );
        const defaultTemplateId = normalizedTemplateOptions.some(
          (option) => option.id === configPayload.active_template,
        )
          ? configPayload.active_template
          : (normalizedTemplateOptions[0]?.id ?? "");

        setConfig(configPayload);
        setSections(sectionsPayload);
        setSelectedTemplateId(configPayload.active_template);
        setContentTemplateId(defaultTemplateId);
        setContentPageFilter("all");
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

    void loadPortalData();

    return () => {
      mounted = false;
    };
  }, []);

  useEffect(() => {
    if (filteredSections.length === 0) {
      setSelectedSectionId("");
      return;
    }

    setSelectedSectionId((previous) => {
      const alreadyExists = filteredSections.some(
        (section) => String(section.id) === previous,
      );
      if (alreadyExists) {
        return previous;
      }
      return String(filteredSections[0].id);
    });
  }, [filteredSections]);

  useEffect(() => {
    if (!selectedSection) {
      setSectionTitleDraft("");
      setSectionSortOrderDraft("0");
      setSectionEnabledDraft(true);
      setSectionBodyJsonDraft("{}");
      return;
    }

    setSectionTitleDraft(selectedSection.title);
    setSectionSortOrderDraft(String(selectedSection.sort_order));
    setSectionEnabledDraft(selectedSection.is_enabled);
    setSectionBodyJsonDraft(stringifyBodyJson(selectedSection.body_json));
  }, [selectedSection]);

  const showAll = activeSection === "all";

  async function handleRefreshSections() {
    setRefreshingSections(true);
    setErrorMessage("");
    setSuccessMessage("");

    try {
      const sectionsPayload = await listPortalSectionsAdmin();
      setSections(sectionsPayload);
      setSuccessMessage("Conteudo dinamico atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setRefreshingSections(false);
    }
  }

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
      setContentTemplateId(updatedConfig.active_template);
      setSuccessMessage("Template ativo atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleSaveSection() {
    if (!selectedSection) {
      return;
    }

    setSavingSection(true);
    setSuccessMessage("");
    setErrorMessage("");

    try {
      const parsedSortOrder = Number.parseInt(sectionSortOrderDraft, 10);
      if (Number.isNaN(parsedSortOrder) || parsedSortOrder < 0) {
        throw new Error("Informe um sort_order valido (0 ou maior).");
      }

      let parsedBodyJson: unknown;
      try {
        parsedBodyJson = parseBodyJson(sectionBodyJsonDraft);
      } catch {
        throw new Error("JSON invalido no body_json da secao.");
      }

      const updatedSection = await updatePortalSectionAdmin(selectedSection.id, {
        title: sectionTitleDraft.trim(),
        sort_order: parsedSortOrder,
        is_enabled: sectionEnabledDraft,
        body_json: parsedBodyJson,
      });

      setSections((previous) =>
        previous.map((section) =>
          section.id === updatedSection.id ? updatedSection : section,
        ),
      );
      setSuccessMessage(
        `Secao ${updatedSection.key} atualizada com sucesso para o template ${updatedSection.template_id}.`,
      );
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingSection(false);
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
      setContentTemplateId(publishedConfig.active_template);
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
              Controle do template ativo, seções dinamicas e publicacao do portal.
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
          <div className="mt-4 grid gap-3 md:grid-cols-4">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Template ativo</p>
              <p className="mt-1 text-base font-semibold text-text">{activeTemplateLabel}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Templates disponiveis</p>
              <p className="mt-1 text-base font-semibold text-text">{templateOptions.length}</p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Secoes CMS</p>
              <p className="mt-1 text-base font-semibold text-text">{sections.length}</p>
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

      {(showAll || activeSection === "conteudo") && (
        <section id="conteudo" className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Conteudo dinamico</h2>
              <p className="mt-1 text-sm text-muted">
                Edite textos, links e fotos das secoes por template e pagina.
              </p>
            </div>
            <button
              type="button"
              onClick={() => void handleRefreshSections()}
              disabled={refreshingSections}
              className="rounded-xl border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {refreshingSections ? "Atualizando..." : "Atualizar secoes"}
            </button>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <label className="grid gap-1 text-sm text-muted">
              Template
              <select
                value={contentTemplateId}
                onChange={(event) => setContentTemplateId(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                {templateOptions.map((option) => (
                  <option key={option.id} value={option.id}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm text-muted">
              Pagina
              <select
                value={contentPageFilter}
                onChange={(event) => setContentPageFilter(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
              >
                {pageOptions.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>

            <label className="grid gap-1 text-sm text-muted">
              Secao
              <select
                value={selectedSectionId}
                onChange={(event) => setSelectedSectionId(event.currentTarget.value)}
                className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                disabled={filteredSections.length === 0}
              >
                {filteredSections.length === 0 && (
                  <option value="">Nenhuma secao encontrada</option>
                )}
                {filteredSections.map((section) => (
                  <option key={section.id} value={section.id}>
                    {section.key} | {formatPortalPageLabel(section.page)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          {selectedSection && (
            <div className="mt-4 grid gap-4 lg:grid-cols-[1fr_320px]">
              <div className="rounded-xl border border-border bg-bg p-4">
                <div className="grid gap-3 sm:grid-cols-2">
                  <label className="grid gap-1 text-sm text-muted">
                    Titulo da secao
                    <input
                      value={sectionTitleDraft}
                      onChange={(event) => setSectionTitleDraft(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Ordenacao (sort_order)
                    <input
                      type="number"
                      min={0}
                      value={sectionSortOrderDraft}
                      onChange={(event) => setSectionSortOrderDraft(event.currentTarget.value)}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                </div>

                <label className="mt-3 inline-flex items-center gap-2 text-sm text-text">
                  <input
                    type="checkbox"
                    checked={sectionEnabledDraft}
                    onChange={(event) => setSectionEnabledDraft(event.currentTarget.checked)}
                    className="h-4 w-4 rounded border-border text-primary"
                  />
                  Secao habilitada
                </label>

                <label className="mt-3 grid gap-1 text-sm text-muted">
                  body_json (JSON dinamico)
                  <textarea
                    rows={18}
                    value={sectionBodyJsonDraft}
                    onChange={(event) => setSectionBodyJsonDraft(event.currentTarget.value)}
                    className="rounded-md border border-border bg-bg px-3 py-2 font-mono text-xs text-text"
                  />
                </label>

                <div className="mt-4 flex justify-end">
                  <button
                    type="button"
                    onClick={() => void handleSaveSection()}
                    disabled={savingSection}
                    className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                  >
                    {savingSection ? "Salvando..." : "Salvar secao"}
                  </button>
                </div>
              </div>

              <aside className="rounded-xl border border-border bg-bg p-4 text-xs text-muted">
                <p className="font-semibold text-text">Referencia rapida (LetsFit)</p>
                <p className="mt-2">
                  <strong className="text-text">hero:</strong> kicker, headline, subheadline,
                  background_image_url, cta_primary, cta_secondary.
                </p>
                <p className="mt-2">
                  <strong className="text-text">categories:</strong> items com name,
                  description e image_url.
                </p>
                <p className="mt-2">
                  <strong className="text-text">benefits:</strong> items como texto ou objeto com
                  text e icon.
                </p>
                <p className="mt-2">
                  <strong className="text-text">kit:</strong> kicker, headline, description,
                  cta_label, cta_href.
                </p>
                <p className="mt-2">
                  <strong className="text-text">how_to_heat:</strong> title, subheadline,
                  <code> cards[&#123;title,description,tone&#125;]</code>.
                </p>
                <p className="mt-2">
                  <strong className="text-text">faq:</strong>
                  <code> items[&#123;question,answer&#125;]</code>.
                </p>
              </aside>
            </div>
          )}
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

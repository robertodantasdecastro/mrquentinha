"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  cancelInstallerJobAdmin,
  getInstallerJobStatusAdmin,
  listInstallerJobsAdmin,
  saveInstallerWizardAdmin,
  startInstallerJobAdmin,
  updatePortalConfigAdmin,
  validateInstallerWizardAdmin,
} from "@/lib/api";
import type {
  PortalConfigData,
  PortalInstallerDraftPayload,
  PortalInstallerJobData,
  PortalInstallerPrerequisites,
  PortalInstallerSettingsConfig,
  PortalPaymentProvidersConfig,
} from "@/types/api";

type InstallAssistantPanelProps = {
  config: PortalConfigData | null;
  onConfigUpdated?: (nextConfig: PortalConfigData) => void;
};

type WizardStep = {
  id: string;
  title: string;
  description: string;
};

const WIZARD_STEPS: WizardStep[] = [
  {
    id: "mode",
    title: "Modo de operacao",
    description: "Defina ambiente (dev/prod), stack (vm/docker) e start automatico.",
  },
  {
    id: "target",
    title: "Destino da instalacao",
    description: "Escolha local, SSH remoto ou cloud (AWS/GCP).",
  },
  {
    id: "infra",
    title: "Infraestrutura",
    description: "Configure parametros de conexao SSH ou cloud.",
  },
  {
    id: "deployment",
    title: "Aplicacao e dominios",
    description: "Informe dados da loja, dominios e modo de seed inicial.",
  },
  {
    id: "lifecycle",
    title: "Workflow continuo",
    description: "Defina regras de sincronizacao continua do instalador.",
  },
  {
    id: "review",
    title: "Revisao final",
    description: "Revise o plano antes de iniciar.",
  },
  {
    id: "execute",
    title: "Execucao",
    description: "Execute e acompanhe logs/status em tempo real.",
  },
];

type DnsPrerequisiteDraft = {
  root_domain: string;
  portal_domain: string;
  client_domain: string;
  admin_domain: string;
  api_domain: string;
};

type PaymentPrerequisiteDraft = {
  web_provider: string;
  mobile_provider: string;
  receiver_person_type: "CPF" | "CNPJ";
  receiver_document: string;
  receiver_name: string;
  receiver_email: string;
  mercadopago_access_token: string;
  efi_client_id: string;
  efi_client_secret: string;
  asaas_api_key: string;
};

const PRODUCTION_PAYMENT_PROVIDER_OPTIONS = [
  { value: "mercadopago", label: "Mercado Pago" },
  { value: "efi", label: "Efi" },
  { value: "asaas", label: "Asaas" },
];

function getDefaultPaymentProviders(): PortalPaymentProvidersConfig {
  return {
    default_provider: "mock",
    enabled_providers: ["mock"],
    frontend_provider: {
      web: "mock",
      mobile: "mock",
    },
    method_provider_order: {
      PIX: ["mock"],
      CARD: ["mock"],
      VR: ["mock"],
    },
    receiver: {
      person_type: "CNPJ",
      document: "",
      name: "",
      email: "",
    },
    mercadopago: {
      enabled: false,
      api_base_url: "https://api.mercadopago.com",
      access_token: "",
      webhook_secret: "",
      sandbox: true,
    },
    efi: {
      enabled: false,
      api_base_url: "https://cobrancas-h.api.efipay.com.br",
      client_id: "",
      client_secret: "",
      webhook_secret: "",
      sandbox: true,
    },
    asaas: {
      enabled: false,
      api_base_url: "https://sandbox.asaas.com/api/v3",
      api_key: "",
      webhook_secret: "",
      sandbox: true,
    },
  };
}

function normalizePaymentProviders(
  value: PortalPaymentProvidersConfig | null | undefined,
): PortalPaymentProvidersConfig {
  const defaults = getDefaultPaymentProviders();
  return {
    ...defaults,
    ...(value ?? {}),
    frontend_provider: {
      ...defaults.frontend_provider,
      ...(value?.frontend_provider ?? {}),
    },
    method_provider_order: {
      ...defaults.method_provider_order,
      ...(value?.method_provider_order ?? {}),
    },
    receiver: {
      ...defaults.receiver,
      ...(value?.receiver ?? {}),
    },
    mercadopago: {
      ...defaults.mercadopago,
      ...(value?.mercadopago ?? {}),
    },
    efi: {
      ...defaults.efi,
      ...(value?.efi ?? {}),
    },
    asaas: {
      ...defaults.asaas,
      ...(value?.asaas ?? {}),
    },
  };
}

function getDefaultDnsPrerequisiteDraft(): DnsPrerequisiteDraft {
  return {
    root_domain: "",
    portal_domain: "",
    client_domain: "",
    admin_domain: "",
    api_domain: "",
  };
}

function getDefaultPaymentPrerequisiteDraft(): PaymentPrerequisiteDraft {
  return {
    web_provider: "mercadopago",
    mobile_provider: "mercadopago",
    receiver_person_type: "CNPJ",
    receiver_document: "",
    receiver_name: "",
    receiver_email: "",
    mercadopago_access_token: "",
    efi_client_id: "",
    efi_client_secret: "",
    asaas_api_key: "",
  };
}

function getDefaultDraft(): PortalInstallerDraftPayload {
  return {
    mode: "dev",
    stack: "vm",
    target: "local",
    start_after_install: false,
    ssh: {
      host: "",
      port: 22,
      user: "",
      auth_mode: "key",
      key_path: "",
      password: "",
    },
    cloud: {
      provider: "aws",
      region: "",
      instance_type: "",
      ami: "",
      key_pair_name: "",
      use_elastic_ip: true,
    },
    deployment: {
      store_name: "Mr Quentinha",
      root_domain: "mrquentinha.com.br",
      portal_domain: "www.mrquentinha.com.br",
      client_domain: "app.mrquentinha.com.br",
      admin_domain: "admin.mrquentinha.com.br",
      api_domain: "api.mrquentinha.com.br",
      seed_mode: "empty",
    },
    lifecycle: {
      enforce_sync_memory: true,
      enforce_quality_gate: true,
      enforce_installer_workflow_check: true,
    },
  };
}

function getDefaultSettings(): PortalInstallerSettingsConfig {
  return {
    workflow_version: "2026.02.28",
    last_synced_at: "",
    last_sync_note: "Workflow do instalador ainda nao sincronizado.",
    requires_review: false,
    lifecycle: {
      enforce_sync_memory: true,
      enforce_quality_gate: true,
      enforce_installer_workflow_check: true,
    },
    wizard: {
      autosave_enabled: true,
      last_completed_step: "mode",
      draft: getDefaultDraft(),
    },
    jobs: {
      last_job_id: "",
      last_job_status: "idle",
      last_job_started_at: "",
      last_job_finished_at: "",
      last_job_summary: "",
    },
  };
}

function normalizeInstallerSettings(
  value: PortalInstallerSettingsConfig | null | undefined,
): PortalInstallerSettingsConfig {
  const defaults = getDefaultSettings();
  if (!value) {
    return defaults;
  }
  return {
    ...defaults,
    ...value,
    lifecycle: {
      ...defaults.lifecycle,
      ...(value.lifecycle ?? {}),
    },
    wizard: {
      ...defaults.wizard,
      ...(value.wizard ?? {}),
      draft: {
        ...defaults.wizard.draft,
        ...(value.wizard?.draft ?? {}),
        ssh: {
          ...defaults.wizard.draft.ssh,
          ...(value.wizard?.draft?.ssh ?? {}),
        },
        cloud: {
          ...defaults.wizard.draft.cloud,
          ...(value.wizard?.draft?.cloud ?? {}),
        },
        deployment: {
          ...defaults.wizard.draft.deployment,
          ...(value.wizard?.draft?.deployment ?? {}),
        },
        lifecycle: {
          ...defaults.wizard.draft.lifecycle,
          ...(value.wizard?.draft?.lifecycle ?? {}),
        },
      },
    },
    jobs: {
      ...defaults.jobs,
      ...(value.jobs ?? {}),
    },
  };
}

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada no assistente de instalacao.";
}

function getJobTone(status: string): "success" | "warning" | "danger" | "info" | "neutral" {
  if (status === "running") {
    return "info";
  }
  if (status === "succeeded") {
    return "success";
  }
  if (status === "failed" || status === "canceled") {
    return "danger";
  }
  if (status === "planned" || status === "finished") {
    return "warning";
  }
  return "neutral";
}

export function InstallAssistantPanel({
  config,
  onConfigUpdated,
}: InstallAssistantPanelProps) {
  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [draft, setDraft] = useState<PortalInstallerDraftPayload>(getDefaultDraft());
  const [settings, setSettings] = useState<PortalInstallerSettingsConfig>(getDefaultSettings());
  const [recentJobs, setRecentJobs] = useState<PortalInstallerJobData[]>([]);
  const [activeJob, setActiveJob] = useState<PortalInstallerJobData | null>(null);
  const [prerequisites, setPrerequisites] = useState<PortalInstallerPrerequisites | null>(null);
  const [showPrerequisitesModal, setShowPrerequisitesModal] = useState(false);
  const [dnsDraft, setDnsDraft] = useState<DnsPrerequisiteDraft>(getDefaultDnsPrerequisiteDraft());
  const [paymentDraft, setPaymentDraft] = useState<PaymentPrerequisiteDraft>(
    getDefaultPaymentPrerequisiteDraft(),
  );
  const [warnings, setWarnings] = useState<string[]>([]);
  const [loadingJobs, setLoadingJobs] = useState(false);
  const [validating, setValidating] = useState(false);
  const [saving, setSaving] = useState(false);
  const [starting, setStarting] = useState(false);
  const [canceling, setCanceling] = useState(false);
  const [savingPrerequisites, setSavingPrerequisites] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  const currentStep = WIZARD_STEPS[currentStepIndex] ?? WIZARD_STEPS[0];
  const progressPercent = useMemo(() => {
    if (WIZARD_STEPS.length <= 1) {
      return 100;
    }
    return Math.round((currentStepIndex / (WIZARD_STEPS.length - 1)) * 100);
  }, [currentStepIndex]);

  const selectedProductionProviders = useMemo(() => {
    const providers = new Set<string>();
    for (const provider of [paymentDraft.web_provider, paymentDraft.mobile_provider]) {
      const normalized = provider.trim().toLowerCase();
      if (normalized === "mercadopago" || normalized === "efi" || normalized === "asaas") {
        providers.add(normalized);
      }
    }
    return Array.from(providers);
  }, [paymentDraft.mobile_provider, paymentDraft.web_provider]);

  useEffect(() => {
    const normalizedSettings = normalizeInstallerSettings(config?.installer_settings);
    setSettings(normalizedSettings);
    setDraft(normalizedSettings.wizard.draft);

    const savedStepIndex = WIZARD_STEPS.findIndex(
      (step) => step.id === normalizedSettings.wizard.last_completed_step,
    );
    if (savedStepIndex >= 0) {
      setCurrentStepIndex(savedStepIndex);
    }
  }, [config]);

  useEffect(() => {
    if (!config || showPrerequisitesModal) {
      return;
    }

    setDnsDraft({
      root_domain: config.root_domain ?? "",
      portal_domain: config.portal_domain ?? "",
      client_domain: config.client_domain ?? "",
      admin_domain: config.admin_domain ?? "",
      api_domain: config.api_domain ?? "",
    });

    const paymentProviders = normalizePaymentProviders(config.payment_providers);
    const webProvider = paymentProviders.frontend_provider.web;
    const mobileProvider = paymentProviders.frontend_provider.mobile;
    setPaymentDraft({
      web_provider:
        webProvider === "mock" ? "mercadopago" : webProvider,
      mobile_provider:
        mobileProvider === "mock" ? "mercadopago" : mobileProvider,
      receiver_person_type: paymentProviders.receiver.person_type,
      receiver_document: paymentProviders.receiver.document ?? "",
      receiver_name: paymentProviders.receiver.name ?? "",
      receiver_email: paymentProviders.receiver.email ?? "",
      mercadopago_access_token: paymentProviders.mercadopago.access_token ?? "",
      efi_client_id: paymentProviders.efi.client_id ?? "",
      efi_client_secret: paymentProviders.efi.client_secret ?? "",
      asaas_api_key: paymentProviders.asaas.api_key ?? "",
    });
  }, [config, showPrerequisitesModal]);

  useEffect(() => {
    let cancelled = false;
    async function loadJobs() {
      setLoadingJobs(true);
      try {
        const payload = await listInstallerJobsAdmin();
        if (!cancelled) {
          setRecentJobs(payload.results ?? []);
        }
      } catch {
        // Mantem silencioso para nao interromper o assistente.
      } finally {
        if (!cancelled) {
          setLoadingJobs(false);
        }
      }
    }
    void loadJobs();
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!activeJob?.job_id) {
      return;
    }
    if (activeJob.status !== "running") {
      return;
    }

    const interval = window.setInterval(() => {
      void (async () => {
        try {
          const payload = await getInstallerJobStatusAdmin(activeJob.job_id);
          setActiveJob(payload.job);
          onConfigUpdated?.(payload.config);
        } catch {
          // Nao interrompe a UX em caso de falha pontual de polling.
        }
      })();
    }, 5000);

    return () => {
      window.clearInterval(interval);
    };
  }, [activeJob, onConfigUpdated]);

  function updateDraft(nextDraft: Partial<PortalInstallerDraftPayload>) {
    setDraft((current) => ({
      ...current,
      ...nextDraft,
    }));
  }

  function updateSshDraft(nextSsh: Partial<PortalInstallerDraftPayload["ssh"]>) {
    setDraft((current) => ({
      ...current,
      ssh: {
        ...current.ssh,
        ...nextSsh,
      },
    }));
  }

  function updateCloudDraft(nextCloud: Partial<PortalInstallerDraftPayload["cloud"]>) {
    setDraft((current) => ({
      ...current,
      cloud: {
        ...current.cloud,
        ...nextCloud,
      },
    }));
  }

  function updateDeploymentDraft(
    nextDeployment: Partial<PortalInstallerDraftPayload["deployment"]>,
  ) {
    setDraft((current) => ({
      ...current,
      deployment: {
        ...current.deployment,
        ...nextDeployment,
      },
    }));
  }

  function updateLifecycleDraft(
    nextLifecycle: Partial<PortalInstallerDraftPayload["lifecycle"]>,
  ) {
    setDraft((current) => ({
      ...current,
      lifecycle: {
        ...current.lifecycle,
        ...nextLifecycle,
      },
    }));
  }

  function openPrerequisitesModal() {
    setShowPrerequisitesModal(true);
    setErrorMessage("");
    setSuccessMessage("");
  }

  function applyValidationResult(result: {
    normalized_payload: PortalInstallerDraftPayload;
    warnings?: string[];
    prerequisites?: PortalInstallerPrerequisites;
  }) {
    setDraft(result.normalized_payload);
    setWarnings(result.warnings ?? []);
    const nextPrerequisites = result.prerequisites ?? null;
    setPrerequisites(nextPrerequisites);
    if (
      nextPrerequisites &&
      nextPrerequisites.mode === "prod" &&
      !nextPrerequisites.ready
    ) {
      setShowPrerequisitesModal(true);
    }
  }

  async function handleSavePrerequisites() {
    if (!config) {
      return;
    }

    setSavingPrerequisites(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const currentPayment = normalizePaymentProviders(config.payment_providers);
      const enabledProviders = selectedProductionProviders;
      const defaultProvider = enabledProviders[0] ?? currentPayment.default_provider;
      const nextPaymentProviders: PortalPaymentProvidersConfig = {
        ...currentPayment,
        default_provider: defaultProvider,
        enabled_providers: enabledProviders,
        frontend_provider: {
          web: paymentDraft.web_provider,
          mobile: paymentDraft.mobile_provider,
        },
        receiver: {
          person_type: paymentDraft.receiver_person_type,
          document: paymentDraft.receiver_document.trim(),
          name: paymentDraft.receiver_name.trim(),
          email: paymentDraft.receiver_email.trim(),
        },
        mercadopago: {
          ...currentPayment.mercadopago,
          enabled: enabledProviders.includes("mercadopago"),
          access_token: paymentDraft.mercadopago_access_token.trim(),
        },
        efi: {
          ...currentPayment.efi,
          enabled: enabledProviders.includes("efi"),
          client_id: paymentDraft.efi_client_id.trim(),
          client_secret: paymentDraft.efi_client_secret.trim(),
        },
        asaas: {
          ...currentPayment.asaas,
          enabled: enabledProviders.includes("asaas"),
          api_key: paymentDraft.asaas_api_key.trim(),
        },
      };

      const updatedConfig = await updatePortalConfigAdmin(config.id, {
        root_domain: dnsDraft.root_domain.trim(),
        portal_domain: dnsDraft.portal_domain.trim(),
        client_domain: dnsDraft.client_domain.trim(),
        admin_domain: dnsDraft.admin_domain.trim(),
        api_domain: dnsDraft.api_domain.trim(),
        payment_providers: nextPaymentProviders,
      });
      onConfigUpdated?.(updatedConfig);

      const validation = await validateInstallerWizardAdmin(draft);
      applyValidationResult(validation);

      if (validation.prerequisites?.ready) {
        setShowPrerequisitesModal(false);
        setSuccessMessage("Pre-requisitos atualizados e validados para producao.");
      } else {
        setErrorMessage(
          "Ainda existem pre-requisitos pendentes. Revise os campos obrigatorios.",
        );
      }
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingPrerequisites(false);
    }
  }

  function validateCurrentStepLocally(): string | null {
    if (currentStep.id === "target" && draft.target === "ssh") {
      if (!draft.ssh.host.trim()) {
        return "Informe o host remoto para instalacao via SSH.";
      }
      if (!draft.ssh.user.trim()) {
        return "Informe o usuario remoto para instalacao via SSH.";
      }
    }

    if (currentStep.id === "infra" && (draft.target === "aws" || draft.target === "gcp")) {
      if (!draft.cloud.region.trim()) {
        return "Informe a regiao da cloud para continuar.";
      }
    }

    if (currentStep.id === "deployment") {
      if (!draft.deployment.root_domain.trim()) {
        return "Informe o dominio raiz da operacao.";
      }
      if (!draft.deployment.api_domain.trim()) {
        return "Informe o dominio da API.";
      }
    }

    return null;
  }

  async function handleValidateWithBackend() {
    setValidating(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const result = await validateInstallerWizardAdmin(draft);
      applyValidationResult(result);
      if (result.prerequisites && result.prerequisites.mode === "prod" && !result.prerequisites.ready) {
        setErrorMessage(
          "Pre-requisitos de producao pendentes. Complete DNS/servidor e pagamentos no modal.",
        );
      } else {
        setSuccessMessage("Validacao concluida. Configure os ajustes e siga para o proximo passo.");
      }
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setValidating(false);
    }
  }

  async function handleSaveDraft(nextStepId: string) {
    setSaving(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const updatedConfig = await saveInstallerWizardAdmin({
        payload: draft,
        completedStep: nextStepId,
      });
      onConfigUpdated?.(updatedConfig);
      setSettings(normalizeInstallerSettings(updatedConfig.installer_settings));
      setSuccessMessage("Draft do assistente salvo.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSaving(false);
    }
  }

  async function handleNextStep() {
    const localValidationError = validateCurrentStepLocally();
    if (localValidationError) {
      setErrorMessage(localValidationError);
      return;
    }

    const nextIndex = Math.min(currentStepIndex + 1, WIZARD_STEPS.length - 1);
    const nextStep = WIZARD_STEPS[nextIndex];
    if (settings.wizard.autosave_enabled && nextStep) {
      await handleSaveDraft(nextStep.id);
    }
    setCurrentStepIndex(nextIndex);
    setErrorMessage("");
  }

  function handlePreviousStep() {
    setCurrentStepIndex((current) => Math.max(current - 1, 0));
    setErrorMessage("");
  }

  async function handleStartJob() {
    setStarting(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const validation = await validateInstallerWizardAdmin(draft);
      applyValidationResult(validation);
      if (validation.prerequisites?.mode === "prod" && !validation.prerequisites.ready) {
        setErrorMessage(
          "Execucao bloqueada: pre-requisitos de producao pendentes. Ajuste no modal e tente novamente.",
        );
        setShowPrerequisitesModal(true);
        return;
      }

      const payload = await startInstallerJobAdmin(validation.normalized_payload);
      setActiveJob(payload.job);
      onConfigUpdated?.(payload.config);
      setSuccessMessage("Job do instalador iniciado.");
      const refreshedJobs = await listInstallerJobsAdmin();
      setRecentJobs(refreshedJobs.results ?? []);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setStarting(false);
    }
  }

  async function handleRefreshActiveJob() {
    if (!activeJob?.job_id) {
      return;
    }
    try {
      const payload = await getInstallerJobStatusAdmin(activeJob.job_id);
      setActiveJob(payload.job);
      onConfigUpdated?.(payload.config);
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    }
  }

  async function handleCancelActiveJob() {
    if (!activeJob?.job_id) {
      return;
    }
    setCanceling(true);
    setErrorMessage("");
    setSuccessMessage("");
    try {
      const payload = await cancelInstallerJobAdmin(activeJob.job_id);
      setActiveJob(payload.job);
      onConfigUpdated?.(payload.config);
      setSuccessMessage("Job cancelado.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setCanceling(false);
    }
  }

  return (
    <section
      id="assistente-instalacao"
      className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
    >
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-text">Assistente de instalacao e deploy</h2>
          <p className="mt-1 text-sm text-muted">
            Fluxo guiado em etapas para operadores sem conhecimento tecnico avancado.
          </p>
        </div>
        <div className="text-right text-xs text-muted">
          <p>
            Workflow: <strong className="text-text">{settings.workflow_version}</strong>
          </p>
          <p className="mt-1">
            Ultima sincronizacao:{" "}
            <strong className="text-text">
              {settings.last_synced_at ? new Date(settings.last_synced_at).toLocaleString("pt-BR") : "-"}
            </strong>
          </p>
          <p className="mt-1">{settings.last_sync_note}</p>
        </div>
      </div>

      {(validating || saving || starting || canceling) && (
        <InlinePreloader message="Processando assistente..." />
      )}

      {errorMessage && (
        <p className="mt-4 rounded-md border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-700">
          {errorMessage}
        </p>
      )}
      {successMessage && (
        <p className="mt-4 rounded-md border border-emerald-500/40 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-700">
          {successMessage}
        </p>
      )}
      {warnings.length > 0 && (
        <div className="mt-4 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-amber-700">
          {warnings.map((warning) => (
            <p key={warning}>- {warning}</p>
          ))}
        </div>
      )}
      {prerequisites && prerequisites.mode === "prod" && !prerequisites.ready && (
        <div className="mt-4 rounded-md border border-rose-500/40 bg-rose-500/10 px-3 py-2 text-sm text-rose-700">
          <p className="font-semibold">
            Producao bloqueada: {prerequisites.missing_count} pendencia(s) de pre-requisito.
          </p>
          <p className="mt-1">
            Resolva DNS/servidor e gateway de pagamento antes de iniciar deploy.
          </p>
          <button
            type="button"
            onClick={openPrerequisitesModal}
            className="mt-2 rounded-md border border-rose-500/40 bg-rose-500/5 px-3 py-1.5 text-xs font-semibold text-rose-700 transition hover:bg-rose-500/10"
          >
            Abrir modal de pre-requisitos
          </button>
        </div>
      )}

      <div className="mt-5 rounded-xl border border-border bg-bg p-4">
        <div className="flex items-center justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.12em] text-primary">
              Passo {currentStepIndex + 1} de {WIZARD_STEPS.length}
            </p>
            <h3 className="mt-1 text-base font-semibold text-text">{currentStep.title}</h3>
            <p className="mt-1 text-xs text-muted">{currentStep.description}</p>
          </div>
          <StatusPill tone={settings.requires_review ? "warning" : "success"}>
            {settings.requires_review ? "Revisar workflow" : "Workflow sincronizado"}
          </StatusPill>
        </div>

        <div className="mt-3 h-2 overflow-hidden rounded-full bg-surface">
          <div
            className="h-full rounded-full bg-primary transition-all duration-500"
            style={{ width: `${progressPercent}%` }}
          />
        </div>

        <ol className="mt-4 grid gap-2 md:grid-cols-4 xl:grid-cols-7">
          {WIZARD_STEPS.map((step, index) => (
            <li key={step.id}>
              <button
                type="button"
                onClick={() => setCurrentStepIndex(index)}
                className={[
                  "w-full rounded-md border px-2 py-2 text-left text-xs transition",
                  index === currentStepIndex
                    ? "border-primary bg-primary/10 text-primary"
                    : index < currentStepIndex
                      ? "border-emerald-400/40 bg-emerald-500/10 text-emerald-700"
                      : "border-border bg-surface text-muted hover:border-primary/40",
                ].join(" ")}
              >
                <p className="font-semibold">{index + 1}. {step.title}</p>
              </button>
            </li>
          ))}
        </ol>

        <div className="mt-4 rounded-lg border border-border bg-surface/60 p-4">
          {currentStep.id === "mode" && (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-4">
              <label className="grid gap-1 text-sm text-muted">
                Ambiente
                <select
                  value={draft.mode}
                  onChange={(event) =>
                    updateDraft({ mode: event.currentTarget.value as PortalInstallerDraftPayload["mode"] })
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="dev">Desenvolvimento (dev)</option>
                  <option value="prod">Producao (prod)</option>
                </select>
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Stack
                <select
                  value={draft.stack}
                  onChange={(event) =>
                    updateDraft({ stack: event.currentTarget.value as PortalInstallerDraftPayload["stack"] })
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="vm">VM (padrao)</option>
                  <option value="docker">Docker (opcional)</option>
                </select>
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Destino preferencial
                <select
                  value={draft.target}
                  onChange={(event) =>
                    updateDraft({ target: event.currentTarget.value as PortalInstallerDraftPayload["target"] })
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="local">Maquina local</option>
                  <option value="ssh">Servidor remoto (SSH)</option>
                  <option value="aws">Cloud AWS</option>
                  <option value="gcp">Cloud Google</option>
                </select>
              </label>
              <label className="mt-6 inline-flex items-center gap-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={draft.start_after_install}
                  onChange={(event) => updateDraft({ start_after_install: event.currentTarget.checked })}
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Iniciar servicos ao finalizar
              </label>
            </div>
          )}

          {currentStep.id === "target" && (
            <div className="grid gap-3 md:grid-cols-2">
              <article className="rounded-lg border border-border bg-bg p-3">
                <p className="text-sm font-semibold text-text">Instalacao local</p>
                <p className="mt-1 text-xs text-muted">
                  Executa o instalador oficial na maquina atual. Ideal para ambiente DEV.
                </p>
              </article>
              <article className="rounded-lg border border-border bg-bg p-3">
                <p className="text-sm font-semibold text-text">Instalacao remota/cloud</p>
                <p className="mt-1 text-xs text-muted">
                  Wizard prepara parametros para SSH, AWS ou GCP e aplica automacoes em fases.
                </p>
              </article>
            </div>
          )}

          {currentStep.id === "infra" && (
            <>
              {draft.target === "ssh" ? (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <label className="grid gap-1 text-sm text-muted">
                    Host SSH
                    <input
                      value={draft.ssh.host}
                      onChange={(event) => updateSshDraft({ host: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="10.0.0.15 ou servidor.exemplo.com"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Porta SSH
                    <input
                      type="number"
                      value={draft.ssh.port}
                      onChange={(event) =>
                        updateSshDraft({ port: Number.parseInt(event.currentTarget.value || "22", 10) || 22 })
                      }
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Usuario SSH
                    <input
                      value={draft.ssh.user}
                      onChange={(event) => updateSshDraft({ user: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="ubuntu"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Autenticacao
                    <select
                      value={draft.ssh.auth_mode}
                      onChange={(event) =>
                        updateSshDraft({ auth_mode: event.currentTarget.value as PortalInstallerDraftPayload["ssh"]["auth_mode"] })
                      }
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    >
                      <option value="key">Chave privada</option>
                      <option value="password">Senha</option>
                    </select>
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Caminho da chave
                    <input
                      value={draft.ssh.key_path}
                      onChange={(event) => updateSshDraft({ key_path: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="~/.ssh/id_ed25519"
                      disabled={draft.ssh.auth_mode !== "key"}
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Senha
                    <input
                      type="password"
                      value={draft.ssh.password}
                      onChange={(event) => updateSshDraft({ password: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      disabled={draft.ssh.auth_mode !== "password"}
                    />
                  </label>
                </div>
              ) : (
                <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                  <label className="grid gap-1 text-sm text-muted">
                    Provider cloud
                    <select
                      value={draft.cloud.provider}
                      onChange={(event) =>
                        updateCloudDraft({ provider: event.currentTarget.value as PortalInstallerDraftPayload["cloud"]["provider"] })
                      }
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    >
                      <option value="aws">AWS</option>
                      <option value="gcp">Google Cloud</option>
                    </select>
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Regiao
                    <input
                      value={draft.cloud.region}
                      onChange={(event) => updateCloudDraft({ region: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="sa-east-1"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Tipo de instancia
                    <input
                      value={draft.cloud.instance_type}
                      onChange={(event) => updateCloudDraft({ instance_type: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="t3.medium"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    AMI / imagem base
                    <input
                      value={draft.cloud.ami}
                      onChange={(event) => updateCloudDraft({ ami: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="ami-xxxxxxxx"
                    />
                  </label>
                  <label className="grid gap-1 text-sm text-muted">
                    Key pair
                    <input
                      value={draft.cloud.key_pair_name}
                      onChange={(event) => updateCloudDraft({ key_pair_name: event.currentTarget.value })}
                      className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      placeholder="mrquentinha-key"
                    />
                  </label>
                  <label className="mt-6 inline-flex items-center gap-2 text-sm text-text">
                    <input
                      type="checkbox"
                      checked={draft.cloud.use_elastic_ip}
                      onChange={(event) => updateCloudDraft({ use_elastic_ip: event.currentTarget.checked })}
                      className="h-4 w-4 rounded border-border text-primary"
                    />
                    Reservar IP elastico/fixo
                  </label>
                </div>
              )}
            </>
          )}

          {currentStep.id === "deployment" && (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <label className="grid gap-1 text-sm text-muted">
                Nome da loja
                <input
                  value={draft.deployment.store_name}
                  onChange={(event) => updateDeploymentDraft({ store_name: event.currentTarget.value })}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominio raiz
                <input
                  value={draft.deployment.root_domain}
                  onChange={(event) => updateDeploymentDraft({ root_domain: event.currentTarget.value })}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominio API
                <input
                  value={draft.deployment.api_domain}
                  onChange={(event) => updateDeploymentDraft({ api_domain: event.currentTarget.value })}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominio portal
                <input
                  value={draft.deployment.portal_domain}
                  onChange={(event) => updateDeploymentDraft({ portal_domain: event.currentTarget.value })}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominio client web
                <input
                  value={draft.deployment.client_domain}
                  onChange={(event) => updateDeploymentDraft({ client_domain: event.currentTarget.value })}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Dominio admin web
                <input
                  value={draft.deployment.admin_domain}
                  onChange={(event) => updateDeploymentDraft({ admin_domain: event.currentTarget.value })}
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                />
              </label>
              <label className="grid gap-1 text-sm text-muted">
                Seed inicial
                <select
                  value={draft.deployment.seed_mode}
                  onChange={(event) =>
                    updateDeploymentDraft({ seed_mode: event.currentTarget.value as PortalInstallerDraftPayload["deployment"]["seed_mode"] })
                  }
                  className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                >
                  <option value="empty">Banco limpo</option>
                  <option value="examples">Banco com exemplos</option>
                </select>
              </label>
            </div>
          )}

          {currentStep.id === "lifecycle" && (
            <div className="grid gap-3 md:grid-cols-2 xl:grid-cols-3">
              <label className="inline-flex items-center gap-2 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={draft.lifecycle.enforce_sync_memory}
                  onChange={(event) =>
                    updateLifecycleDraft({ enforce_sync_memory: event.currentTarget.checked })
                  }
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Exigir `sync_memory --check`
              </label>
              <label className="inline-flex items-center gap-2 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={draft.lifecycle.enforce_quality_gate}
                  onChange={(event) =>
                    updateLifecycleDraft({ enforce_quality_gate: event.currentTarget.checked })
                  }
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Exigir quality gate completo
              </label>
              <label className="inline-flex items-center gap-2 rounded-md border border-border bg-bg px-3 py-2 text-sm text-text">
                <input
                  type="checkbox"
                  checked={draft.lifecycle.enforce_installer_workflow_check}
                  onChange={(event) =>
                    updateLifecycleDraft({
                      enforce_installer_workflow_check: event.currentTarget.checked,
                    })
                  }
                  className="h-4 w-4 rounded border-border text-primary"
                />
                Exigir check de workflow do instalador
              </label>
            </div>
          )}

          {currentStep.id === "review" && (
            <div className="grid gap-2 text-sm text-muted">
              <p>
                <strong className="text-text">Modo:</strong> {draft.mode.toUpperCase()} |{" "}
                <strong className="text-text">Stack:</strong> {draft.stack.toUpperCase()} |{" "}
                <strong className="text-text">Destino:</strong> {draft.target.toUpperCase()}
              </p>
              <p>
                <strong className="text-text">Loja:</strong> {draft.deployment.store_name}
              </p>
              <p>
                <strong className="text-text">Dominio raiz:</strong> {draft.deployment.root_domain}
              </p>
              <p>
                <strong className="text-text">API:</strong> {draft.deployment.api_domain}
              </p>
              <p>
                <strong className="text-text">Seed:</strong>{" "}
                {draft.deployment.seed_mode === "examples" ? "com exemplos" : "limpo"}
              </p>
            </div>
          )}

          {currentStep.id === "execute" && (
            <div className="grid gap-3">
              <div className="flex flex-wrap gap-2">
                <button
                  type="button"
                  onClick={() => void handleStartJob()}
                  disabled={starting}
                  className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
                >
                  {starting ? "Iniciando..." : "Iniciar execucao"}
                </button>
                <button
                  type="button"
                  onClick={() => void handleRefreshActiveJob()}
                  className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
                >
                  Atualizar status
                </button>
                <button
                  type="button"
                  onClick={() => void handleCancelActiveJob()}
                  disabled={!activeJob || canceling}
                  className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
                >
                  {canceling ? "Cancelando..." : "Cancelar job"}
                </button>
              </div>

              {activeJob ? (
                <article className="rounded-md border border-border bg-bg p-3 text-xs text-muted">
                  <div className="flex items-center justify-between gap-2">
                    <p className="font-semibold text-text">Job ativo: {activeJob.job_id}</p>
                    <StatusPill tone={getJobTone(activeJob.status)}>{activeJob.status}</StatusPill>
                  </div>
                  <p className="mt-1">
                    Target: <strong className="text-text">{activeJob.target}</strong> | Mode:{" "}
                    <strong className="text-text">{activeJob.mode}</strong> | Stack:{" "}
                    <strong className="text-text">{activeJob.stack}</strong>
                  </p>
                  <p className="mt-1">{activeJob.summary || "-"}</p>
                  {activeJob.command_preview && (
                    <p className="mt-1">
                      Comando: <code>{activeJob.command_preview}</code>
                    </p>
                  )}
                  {activeJob.last_log_lines && activeJob.last_log_lines.length > 0 && (
                    <div className="mt-2 max-h-48 overflow-auto rounded-md border border-border bg-surface p-2 font-mono">
                      {activeJob.last_log_lines.map((line, index) => (
                        <p key={`${index}-${line}`}>{line}</p>
                      ))}
                    </div>
                  )}
                </article>
              ) : (
                <p className="text-xs text-muted">
                  Nenhum job ativo neste navegador. Use &quot;Atualizar status&quot; para carregar.
                </p>
              )}
            </div>
          )}
        </div>

        <div className="mt-4 flex flex-wrap items-center justify-between gap-2">
          <button
            type="button"
            onClick={handlePreviousStep}
            disabled={currentStepIndex === 0}
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
          >
            Anterior
          </button>
          <div className="flex flex-wrap gap-2">
            <button
              type="button"
              onClick={() => void handleValidateWithBackend()}
              disabled={validating}
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {validating ? "Validando..." : "Validar etapa"}
            </button>
            <button
              type="button"
              onClick={() => void handleSaveDraft(currentStep.id)}
              disabled={saving}
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-60"
            >
              {saving ? "Salvando..." : "Salvar draft"}
            </button>
            <button
              type="button"
              onClick={() => void handleNextStep()}
              disabled={currentStepIndex === WIZARD_STEPS.length - 1}
              className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Proximo
            </button>
          </div>
        </div>
      </div>

      <div className="mt-4 rounded-xl border border-border bg-bg p-4">
        <div className="flex items-center justify-between gap-2">
          <h3 className="text-sm font-semibold text-text">Historico recente de jobs</h3>
          {loadingJobs && <InlinePreloader message="Carregando jobs..." />}
        </div>
        {recentJobs.length === 0 ? (
          <p className="mt-2 text-xs text-muted">Nenhum job registrado ainda.</p>
        ) : (
          <div className="mt-2 grid gap-2">
            {recentJobs.slice(0, 6).map((job) => (
              <article key={job.job_id} className="rounded-md border border-border bg-surface/70 p-2 text-xs">
                <div className="flex items-center justify-between gap-2">
                  <p className="font-semibold text-text">{job.job_id}</p>
                  <StatusPill tone={getJobTone(job.status)}>{job.status}</StatusPill>
                </div>
                <p className="mt-1 text-muted">
                  {job.target} | {job.mode} | {job.stack}
                </p>
                <p className="mt-1 text-muted">{job.summary || "-"}</p>
              </article>
            ))}
          </div>
        )}
      </div>

      {showPrerequisitesModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/55 p-4">
          <div
            role="dialog"
            aria-modal="true"
            className="max-h-[92vh] w-full max-w-4xl overflow-y-auto rounded-2xl border border-border bg-surface p-6 shadow-xl"
          >
            <div className="flex flex-wrap items-start justify-between gap-3">
              <div>
                <h3 className="text-lg font-semibold text-text">
                  Pre-requisitos do modo producao
                </h3>
                <p className="mt-1 text-sm text-muted">
                  Complete DNS/servidor e gateway de pagamento sem sair do assistente.
                </p>
              </div>
              <button
                type="button"
                onClick={() => setShowPrerequisitesModal(false)}
                className="rounded-md border border-border bg-bg px-3 py-1.5 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Fechar
              </button>
            </div>

            {prerequisites && prerequisites.categories.length > 0 && (
              <div className="mt-4 grid gap-2">
                {prerequisites.categories.map((category) => (
                  <article
                    key={category.key}
                    className="rounded-md border border-border bg-bg p-3 text-xs text-muted"
                  >
                    <div className="flex items-center justify-between gap-2">
                      <p className="font-semibold text-text">{category.label}</p>
                      <StatusPill tone={category.ready ? "success" : "danger"}>
                        {category.ready ? "OK" : `${category.missing_fields.length} pendencia(s)`}
                      </StatusPill>
                    </div>
                    <p className="mt-1">{category.description}</p>
                  </article>
                ))}
              </div>
            )}

            <section className="mt-4 rounded-xl border border-border bg-bg p-4">
              <h4 className="text-sm font-semibold text-text">Servidor e DNS</h4>
              <p className="mt-1 text-xs text-muted">
                Estes dados alimentam automaticamente o deploy e os subdominios da plataforma.
              </p>
              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-3">
                <label className="grid gap-1 text-sm text-muted">
                  Dominio raiz
                  <input
                    value={dnsDraft.root_domain}
                    onChange={(event) =>
                      setDnsDraft((current) => ({
                        ...current,
                        root_domain: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Dominio portal
                  <input
                    value={dnsDraft.portal_domain}
                    onChange={(event) =>
                      setDnsDraft((current) => ({
                        ...current,
                        portal_domain: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Dominio web client
                  <input
                    value={dnsDraft.client_domain}
                    onChange={(event) =>
                      setDnsDraft((current) => ({
                        ...current,
                        client_domain: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Dominio web admin
                  <input
                    value={dnsDraft.admin_domain}
                    onChange={(event) =>
                      setDnsDraft((current) => ({
                        ...current,
                        admin_domain: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Dominio API
                  <input
                    value={dnsDraft.api_domain}
                    onChange={(event) =>
                      setDnsDraft((current) => ({
                        ...current,
                        api_domain: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
              </div>
            </section>

            <section className="mt-4 rounded-xl border border-border bg-bg p-4">
              <h4 className="text-sm font-semibold text-text">Gateway de pagamento (producao)</h4>
              <p className="mt-1 text-xs text-muted">
                Defina um provider para web client e outro para app mobile, com credenciais validas.
              </p>
              <div className="mt-3 grid gap-3 md:grid-cols-2 xl:grid-cols-4">
                <label className="grid gap-1 text-sm text-muted">
                  Provider web client
                  <select
                    value={paymentDraft.web_provider}
                    onChange={(event) =>
                      setPaymentDraft((current) => ({
                        ...current,
                        web_provider: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  >
                    {PRODUCTION_PAYMENT_PROVIDER_OPTIONS.map((provider) => (
                      <option key={provider.value} value={provider.value}>
                        {provider.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Provider app mobile
                  <select
                    value={paymentDraft.mobile_provider}
                    onChange={(event) =>
                      setPaymentDraft((current) => ({
                        ...current,
                        mobile_provider: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  >
                    {PRODUCTION_PAYMENT_PROVIDER_OPTIONS.map((provider) => (
                      <option key={provider.value} value={provider.value}>
                        {provider.label}
                      </option>
                    ))}
                  </select>
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Recebedor
                  <select
                    value={paymentDraft.receiver_person_type}
                    onChange={(event) =>
                      setPaymentDraft((current) => ({
                        ...current,
                        receiver_person_type: event.currentTarget.value as "CPF" | "CNPJ",
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  >
                    <option value="CPF">CPF</option>
                    <option value="CNPJ">CNPJ</option>
                  </select>
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Documento
                  <input
                    value={paymentDraft.receiver_document}
                    onChange={(event) =>
                      setPaymentDraft((current) => ({
                        ...current,
                        receiver_document: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  Nome / razao social
                  <input
                    value={paymentDraft.receiver_name}
                    onChange={(event) =>
                      setPaymentDraft((current) => ({
                        ...current,
                        receiver_name: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
                <label className="grid gap-1 text-sm text-muted">
                  E-mail financeiro
                  <input
                    value={paymentDraft.receiver_email}
                    onChange={(event) =>
                      setPaymentDraft((current) => ({
                        ...current,
                        receiver_email: event.currentTarget.value,
                      }))
                    }
                    className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                  />
                </label>
              </div>

              <div className="mt-4 grid gap-3 md:grid-cols-2">
                {selectedProductionProviders.includes("mercadopago") && (
                  <label className="grid gap-1 text-sm text-muted">
                    Access token Mercado Pago
                    <input
                      value={paymentDraft.mercadopago_access_token}
                      onChange={(event) =>
                        setPaymentDraft((current) => ({
                          ...current,
                          mercadopago_access_token: event.currentTarget.value,
                        }))
                      }
                      className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                )}
                {selectedProductionProviders.includes("efi") && (
                  <>
                    <label className="grid gap-1 text-sm text-muted">
                      Client ID Efi
                      <input
                        value={paymentDraft.efi_client_id}
                        onChange={(event) =>
                          setPaymentDraft((current) => ({
                            ...current,
                            efi_client_id: event.currentTarget.value,
                          }))
                        }
                        className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                      />
                    </label>
                    <label className="grid gap-1 text-sm text-muted">
                      Client secret Efi
                      <input
                        value={paymentDraft.efi_client_secret}
                        onChange={(event) =>
                          setPaymentDraft((current) => ({
                            ...current,
                            efi_client_secret: event.currentTarget.value,
                          }))
                        }
                        className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                      />
                    </label>
                  </>
                )}
                {selectedProductionProviders.includes("asaas") && (
                  <label className="grid gap-1 text-sm text-muted">
                    API key Asaas
                    <input
                      value={paymentDraft.asaas_api_key}
                      onChange={(event) =>
                        setPaymentDraft((current) => ({
                          ...current,
                          asaas_api_key: event.currentTarget.value,
                        }))
                      }
                      className="rounded-md border border-border bg-surface px-3 py-2 text-sm text-text"
                    />
                  </label>
                )}
              </div>
            </section>

            <div className="mt-5 flex flex-wrap justify-end gap-2">
              <button
                type="button"
                onClick={() => setShowPrerequisitesModal(false)}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Voltar
              </button>
              <button
                type="button"
                onClick={() => void handleSavePrerequisites()}
                disabled={savingPrerequisites}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {savingPrerequisites ? "Salvando..." : "Salvar pre-requisitos"}
              </button>
            </div>
          </div>
        </div>
      )}
    </section>
  );
}

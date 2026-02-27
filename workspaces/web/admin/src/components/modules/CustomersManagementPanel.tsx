"use client";

import { useEffect, useMemo, useState } from "react";
import { StatusPill } from "@mrquentinha/ui";

import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  createCustomerLgpdRequestAdmin,
  fetchCustomerDetailAdmin,
  fetchCustomersOverviewAdmin,
  listCustomerLgpdRequestsAdmin,
  listCustomersAdmin,
  resendCustomerEmailVerificationAdmin,
  updateCustomerConsentsAdmin,
  updateCustomerGovernanceAdmin,
  updateCustomerLgpdRequestStatusAdmin,
  updateCustomerProfileAdmin,
  updateCustomerStatusAdmin,
} from "@/lib/api";
import type {
  CustomerAccountStatus,
  CustomerData,
  CustomerDetailData,
  CustomerLgpdRequestChannel,
  CustomerLgpdRequestData,
  CustomerLgpdRequestStatus,
  CustomerLgpdRequestType,
  CustomerOverviewData,
} from "@/types/api";

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }
  if (error instanceof Error) {
    return error.message;
  }
  return "Falha inesperada ao carregar gestao de clientes.";
}

function formatDateTime(value: string | null | undefined): string {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }
  return date.toLocaleString("pt-BR");
}

const ACCOUNT_STATUS_OPTIONS: Array<{ value: CustomerAccountStatus; label: string }> = [
  { value: "ACTIVE", label: "Ativa" },
  { value: "UNDER_REVIEW", label: "Em revisao" },
  { value: "SUSPENDED", label: "Suspensa" },
  { value: "BLOCKED", label: "Bloqueada" },
];

const LGPD_REQUEST_TYPE_OPTIONS: Array<{ value: CustomerLgpdRequestType; label: string }> = [
  { value: "ACCESS", label: "Acesso aos dados" },
  { value: "CORRECTION", label: "Correcao" },
  { value: "DELETION", label: "Eliminacao" },
  { value: "ANONYMIZATION", label: "Anonimizacao" },
  { value: "PORTABILITY", label: "Portabilidade" },
  { value: "REVOCATION", label: "Revogacao de consentimento" },
];

const LGPD_CHANNEL_OPTIONS: Array<{ value: CustomerLgpdRequestChannel; label: string }> = [
  { value: "WEB", label: "Web" },
  { value: "APP", label: "App" },
  { value: "EMAIL", label: "E-mail" },
  { value: "WHATSAPP", label: "WhatsApp" },
  { value: "PHONE", label: "Telefone" },
  { value: "IN_PERSON", label: "Presencial" },
];

const LGPD_STATUS_OPTIONS: Array<{ value: CustomerLgpdRequestStatus; label: string }> = [
  { value: "OPEN", label: "Aberta" },
  { value: "IN_PROGRESS", label: "Em andamento" },
  { value: "COMPLETED", label: "Concluida" },
  { value: "REJECTED", label: "Rejeitada" },
];

type ProfileDraft = {
  full_name: string;
  phone: string;
  cpf: string;
  cnpj: string;
  postal_code: string;
  street: string;
  street_number: string;
  neighborhood: string;
  city: string;
  state: string;
  notes: string;
};

const EMPTY_PROFILE_DRAFT: ProfileDraft = {
  full_name: "",
  phone: "",
  cpf: "",
  cnpj: "",
  postal_code: "",
  street: "",
  street_number: "",
  neighborhood: "",
  city: "",
  state: "",
  notes: "",
};

export function CustomersManagementPanel() {
  const [overview, setOverview] = useState<CustomerOverviewData | null>(null);
  const [customers, setCustomers] = useState<CustomerData[]>([]);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [selectedCustomerDetail, setSelectedCustomerDetail] = useState<CustomerDetailData | null>(
    null,
  );
  const [lgpdRequests, setLgpdRequests] = useState<CustomerLgpdRequestData[]>([]);

  const [searchDraft, setSearchDraft] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [complianceFilter, setComplianceFilter] = useState<"" | "pending_email">("");

  const [profileDraft, setProfileDraft] = useState<ProfileDraft>(EMPTY_PROFILE_DRAFT);
  const [statusDraft, setStatusDraft] = useState<CustomerAccountStatus>("ACTIVE");
  const [statusReasonDraft, setStatusReasonDraft] = useState("");
  const [kycStatusDraft, setKycStatusDraft] = useState<"PENDING" | "APPROVED" | "REJECTED">(
    "PENDING",
  );
  const [kycNotesDraft, setKycNotesDraft] = useState("");
  const [acceptedTermsDraft, setAcceptedTermsDraft] = useState(false);
  const [acceptedPrivacyDraft, setAcceptedPrivacyDraft] = useState(false);
  const [marketingOptInDraft, setMarketingOptInDraft] = useState<boolean | null>(null);

  const [lgpdTypeDraft, setLgpdTypeDraft] = useState<CustomerLgpdRequestType>("ACCESS");
  const [lgpdChannelDraft, setLgpdChannelDraft] = useState<CustomerLgpdRequestChannel>("WEB");
  const [lgpdRequesterNameDraft, setLgpdRequesterNameDraft] = useState("");
  const [lgpdRequesterEmailDraft, setLgpdRequesterEmailDraft] = useState("");
  const [lgpdNotesDraft, setLgpdNotesDraft] = useState("");

  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");

  const selectedCustomer = useMemo(
    () => customers.find((customer) => customer.id === selectedCustomerId) ?? null,
    [customers, selectedCustomerId],
  );

  function syncDraftsFromDetail(detail: CustomerDetailData | null) {
    if (!detail) {
      setProfileDraft(EMPTY_PROFILE_DRAFT);
      setStatusDraft("ACTIVE");
      setStatusReasonDraft("");
      setKycStatusDraft("PENDING");
      setKycNotesDraft("");
      return;
    }

    setProfileDraft({
      full_name: detail.profile?.full_name ?? detail.full_name ?? "",
      phone: detail.profile?.phone ?? detail.phone ?? "",
      cpf: detail.profile?.cpf ?? detail.cpf ?? "",
      cnpj: detail.profile?.cnpj ?? detail.cnpj ?? "",
      postal_code: detail.profile?.postal_code ?? "",
      street: detail.profile?.street ?? "",
      street_number: detail.profile?.street_number ?? "",
      neighborhood: detail.profile?.neighborhood ?? "",
      city: detail.profile?.city ?? detail.city ?? "",
      state: detail.profile?.state ?? detail.state ?? "",
      notes: detail.profile?.notes ?? "",
    });

    const governance = detail.governance;
    setStatusDraft(governance?.account_status ?? "ACTIVE");
    setStatusReasonDraft(governance?.account_status_reason ?? "");
    setKycStatusDraft(governance?.kyc_review_status ?? "PENDING");
    setKycNotesDraft(governance?.kyc_review_notes ?? "");
    setAcceptedTermsDraft(Boolean(governance?.terms_accepted_at));
    setAcceptedPrivacyDraft(Boolean(governance?.privacy_policy_accepted_at));
    if (governance?.marketing_opt_in_at) {
      setMarketingOptInDraft(true);
    } else if (governance?.marketing_opt_out_at) {
      setMarketingOptInDraft(false);
    } else {
      setMarketingOptInDraft(null);
    }
  }

  async function loadCustomers(options?: { silent?: boolean }) {
    const silent = options?.silent ?? false;
    if (!silent) {
      setLoading(true);
    }

    try {
      const [overviewPayload, customersPayload] = await Promise.all([
        fetchCustomersOverviewAdmin(),
        listCustomersAdmin({
          search: searchDraft.trim() || undefined,
          account_status: statusFilter || undefined,
          compliance: complianceFilter || undefined,
        }),
      ]);
      setOverview(overviewPayload);
      setCustomers(customersPayload);

      if (customersPayload.length > 0) {
        const nextSelectedId =
          selectedCustomerId && customersPayload.some((item) => item.id === selectedCustomerId)
            ? selectedCustomerId
            : customersPayload[0].id;
        setSelectedCustomerId(nextSelectedId);
      } else {
        setSelectedCustomerId(null);
        setSelectedCustomerDetail(null);
        setLgpdRequests([]);
      }
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setLoading(false);
    }
  }

  async function loadSelectedCustomerDetail(customerId: number) {
    try {
      const [detail, requests] = await Promise.all([
        fetchCustomerDetailAdmin(customerId),
        listCustomerLgpdRequestsAdmin(customerId),
      ]);
      setSelectedCustomerDetail(detail);
      setLgpdRequests(requests);
      syncDraftsFromDetail(detail);
      setErrorMessage("");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    }
  }

  useEffect(() => {
    void loadCustomers();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (!selectedCustomerId) {
      return;
    }
    void loadSelectedCustomerDetail(selectedCustomerId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [selectedCustomerId]);

  async function handleFilterSubmit(event: React.FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await loadCustomers();
  }

  async function handleSaveProfile() {
    if (!selectedCustomerId) {
      return;
    }

    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      await updateCustomerProfileAdmin(selectedCustomerId, profileDraft);
      await loadSelectedCustomerDetail(selectedCustomerId);
      await loadCustomers({ silent: true });
      setMessage("Dados cadastrais do cliente atualizados com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveStatus() {
    if (!selectedCustomerId) {
      return;
    }

    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      await updateCustomerStatusAdmin(selectedCustomerId, {
        account_status: statusDraft,
        reason: statusReasonDraft.trim(),
      });
      await loadSelectedCustomerDetail(selectedCustomerId);
      await loadCustomers({ silent: true });
      setMessage("Status de conta atualizado com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveGovernance() {
    if (!selectedCustomerId) {
      return;
    }

    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      await updateCustomerGovernanceAdmin(selectedCustomerId, {
        kyc_review_status: kycStatusDraft,
        kyc_review_notes: kycNotesDraft.trim(),
      });
      await loadSelectedCustomerDetail(selectedCustomerId);
      setMessage("Governanca/KYC atualizada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleSaveConsents() {
    if (!selectedCustomerId) {
      return;
    }

    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      await updateCustomerConsentsAdmin(selectedCustomerId, {
        accepted_terms: acceptedTermsDraft,
        accepted_privacy_policy: acceptedPrivacyDraft,
        marketing_opt_in: marketingOptInDraft,
      });
      await loadSelectedCustomerDetail(selectedCustomerId);
      await loadCustomers({ silent: true });
      setMessage("Consentimentos LGPD atualizados com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleResendEmailValidation() {
    if (!selectedCustomerId) {
      return;
    }

    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      const result = await resendCustomerEmailVerificationAdmin(selectedCustomerId);
      setMessage(result.detail || "Reenvio de e-mail executado.");
      await loadSelectedCustomerDetail(selectedCustomerId);
      await loadCustomers({ silent: true });
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleCreateLgpdRequest() {
    if (!selectedCustomerId) {
      return;
    }

    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      await createCustomerLgpdRequestAdmin(selectedCustomerId, {
        request_type: lgpdTypeDraft,
        channel: lgpdChannelDraft,
        requested_by_name: lgpdRequesterNameDraft.trim(),
        requested_by_email: lgpdRequesterEmailDraft.trim(),
        notes: lgpdNotesDraft.trim(),
      });
      setLgpdRequesterNameDraft("");
      setLgpdRequesterEmailDraft("");
      setLgpdNotesDraft("");
      await loadSelectedCustomerDetail(selectedCustomerId);
      setMessage("Solicitacao LGPD criada com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  async function handleUpdateLgpdRequestStatus(
    requestId: number,
    statusCode: CustomerLgpdRequestStatus,
  ) {
    setBusy(true);
    setMessage("");
    setErrorMessage("");
    try {
      await updateCustomerLgpdRequestStatusAdmin(requestId, {
        status: statusCode,
      });
      if (selectedCustomerId) {
        await loadSelectedCustomerDetail(selectedCustomerId);
      }
      setMessage("Status da solicitacao LGPD atualizado.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h3 className="text-lg font-semibold text-text">Gestao de Clientes</h3>
          <p className="text-sm text-muted">
            Cadastro, compliance LGPD, status de conta e procedimentos administrativos de e-commerce.
          </p>
        </div>
        <button
          type="button"
          onClick={() => void loadCustomers()}
          disabled={loading || busy}
          className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:cursor-not-allowed disabled:opacity-70"
        >
          Atualizar
        </button>
      </div>

      <form onSubmit={(event) => void handleFilterSubmit(event)} className="mt-4 grid gap-3 md:grid-cols-4">
        <input
          value={searchDraft}
          onChange={(event) => setSearchDraft(event.currentTarget.value)}
          placeholder="Buscar por nome, usuario, e-mail, CPF/CNPJ"
          className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text md:col-span-2"
        />
        <select
          value={statusFilter}
          onChange={(event) => setStatusFilter(event.currentTarget.value)}
          className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
        >
          <option value="">Status de conta (todos)</option>
          {ACCOUNT_STATUS_OPTIONS.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
        <div className="flex gap-2">
          <select
            value={complianceFilter}
            onChange={(event) => setComplianceFilter(event.currentTarget.value as "" | "pending_email")}
            className="w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
          >
            <option value="">Compliance (todos)</option>
            <option value="pending_email">E-mail pendente</option>
          </select>
          <button
            type="submit"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
          >
            Filtrar
          </button>
        </div>
      </form>

      {loading && <InlinePreloader message="Carregando gestão de clientes..." className="mt-4 justify-start bg-surface/70" />}

      {!loading && (
        <>
          {overview && (
            <div className="mt-4 grid gap-3 md:grid-cols-5">
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Clientes</p>
                <p className="mt-1 text-2xl font-semibold text-text">{overview.total}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Ativos</p>
                <p className="mt-1 text-2xl font-semibold text-text">{overview.active}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Inativos</p>
                <p className="mt-1 text-2xl font-semibold text-text">{overview.inactive}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">E-mail pendente</p>
                <p className="mt-1 text-2xl font-semibold text-text">{overview.with_pending_email}</p>
              </article>
              <article className="rounded-xl border border-border bg-bg p-4">
                <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">Conta bloqueada</p>
                <p className="mt-1 text-2xl font-semibold text-text">{overview.by_account_status.BLOCKED ?? 0}</p>
              </article>
            </div>
          )}

          <div className="mt-4 grid gap-4 xl:grid-cols-2">
            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Carteira de clientes</h4>
              <div className="mt-3 space-y-2">
                {customers.map((customer) => {
                  const selected = customer.id === selectedCustomerId;
                  return (
                    <article
                      key={customer.id}
                      className={`rounded-lg border px-3 py-2 ${
                        selected ? "border-primary bg-primary/5" : "border-border bg-surface"
                      }`}
                    >
                      <div className="flex items-start justify-between gap-2">
                        <div>
                          <p className="text-sm font-semibold text-text">
                            {customer.full_name || customer.username}
                          </p>
                          <p className="text-xs text-muted">{customer.email || "sem e-mail"}</p>
                          <p className="text-xs text-muted">
                            Pedidos: {customer.orders_count} | Receita: R$ {customer.orders_total_amount}
                          </p>
                        </div>
                        <button
                          type="button"
                          onClick={() => setSelectedCustomerId(customer.id)}
                          className="rounded-md border border-border bg-bg px-2 py-1 text-xs font-semibold text-text transition hover:border-primary hover:text-primary"
                        >
                          {selected ? "Selecionado" : "Selecionar"}
                        </button>
                      </div>
                      <div className="mt-2 flex flex-wrap gap-2 text-xs">
                        <StatusPill tone={customer.is_active ? "success" : "danger"}>
                          {customer.is_active ? "ativo" : "inativo"}
                        </StatusPill>
                        <StatusPill tone={customer.email_verified ? "success" : "warning"}>
                          {customer.email_verified ? "email ok" : "email pendente"}
                        </StatusPill>
                        <StatusPill tone={customer.checkout_blocked ? "danger" : "success"}>
                          {customer.checkout_blocked ? "checkout bloqueado" : "checkout liberado"}
                        </StatusPill>
                        <StatusPill tone="info">{customer.account_status}</StatusPill>
                      </div>
                    </article>
                  );
                })}
                {customers.length === 0 && (
                  <p className="text-sm text-muted">Nenhum cliente encontrado nos filtros atuais.</p>
                )}
              </div>
            </section>

            <section className="rounded-xl border border-border bg-bg p-4">
              <h4 className="text-base font-semibold text-text">Cliente selecionado</h4>
              {!selectedCustomer && (
                <p className="mt-3 text-sm text-muted">Selecione um cliente para administrar.</p>
              )}
              {selectedCustomer && (
                <div className="mt-3 space-y-4">
                  <article className="rounded-lg border border-border bg-surface p-3">
                    <p className="text-sm font-semibold text-text">
                      {selectedCustomerDetail?.full_name || selectedCustomer.full_name || selectedCustomer.username}
                    </p>
                    <p className="text-xs text-muted">Usuario: {selectedCustomer.username}</p>
                    <p className="text-xs text-muted">E-mail: {selectedCustomer.email || "-"}</p>
                    <p className="text-xs text-muted">
                      Ultimo pedido: {formatDateTime(selectedCustomer.last_order_at)}
                    </p>
                  </article>

                  <article className="rounded-lg border border-border bg-surface p-3">
                    <h5 className="text-sm font-semibold text-text">Status da conta e checkout</h5>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <select
                        value={statusDraft}
                        onChange={(event) => setStatusDraft(event.currentTarget.value as CustomerAccountStatus)}
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      >
                        {ACCOUNT_STATUS_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <button
                        type="button"
                        onClick={() => void handleSaveStatus()}
                        disabled={busy}
                        className="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:opacity-70"
                      >
                        Aplicar status
                      </button>
                    </div>
                    <textarea
                      value={statusReasonDraft}
                      onChange={(event) => setStatusReasonDraft(event.currentTarget.value)}
                      className="mt-2 w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      rows={2}
                      placeholder="Motivo operacional/jurídico da ação"
                    />
                  </article>

                  <article className="rounded-lg border border-border bg-surface p-3">
                    <h5 className="text-sm font-semibold text-text">KYC e revisão documental</h5>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <select
                        value={kycStatusDraft}
                        onChange={(event) =>
                          setKycStatusDraft(event.currentTarget.value as "PENDING" | "APPROVED" | "REJECTED")
                        }
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      >
                        <option value="PENDING">Pendente</option>
                        <option value="APPROVED">Aprovado</option>
                        <option value="REJECTED">Rejeitado</option>
                      </select>
                      <button
                        type="button"
                        onClick={() => void handleSaveGovernance()}
                        disabled={busy}
                        className="rounded-md border border-border px-3 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-70"
                      >
                        Salvar KYC
                      </button>
                    </div>
                    <textarea
                      value={kycNotesDraft}
                      onChange={(event) => setKycNotesDraft(event.currentTarget.value)}
                      className="mt-2 w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      rows={2}
                      placeholder="Observações de revisão documental"
                    />
                  </article>

                  <article className="rounded-lg border border-border bg-surface p-3">
                    <h5 className="text-sm font-semibold text-text">Cadastro essencial</h5>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <input
                        value={profileDraft.full_name}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, full_name: event.currentTarget.value }))
                        }
                        placeholder="Nome completo"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.phone}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, phone: event.currentTarget.value }))
                        }
                        placeholder="Telefone"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.cpf}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, cpf: event.currentTarget.value }))
                        }
                        placeholder="CPF"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.cnpj}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, cnpj: event.currentTarget.value }))
                        }
                        placeholder="CNPJ"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.postal_code}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, postal_code: event.currentTarget.value }))
                        }
                        placeholder="CEP"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.street}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, street: event.currentTarget.value }))
                        }
                        placeholder="Logradouro"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.street_number}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, street_number: event.currentTarget.value }))
                        }
                        placeholder="Número"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.neighborhood}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, neighborhood: event.currentTarget.value }))
                        }
                        placeholder="Bairro"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.city}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, city: event.currentTarget.value }))
                        }
                        placeholder="Cidade"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={profileDraft.state}
                        onChange={(event) =>
                          setProfileDraft((current) => ({ ...current, state: event.currentTarget.value }))
                        }
                        placeholder="UF"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                    </div>
                    <textarea
                      value={profileDraft.notes}
                      onChange={(event) =>
                        setProfileDraft((current) => ({ ...current, notes: event.currentTarget.value }))
                      }
                      className="mt-2 w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      rows={2}
                      placeholder="Observações operacionais"
                    />
                    <div className="mt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={() => void handleSaveProfile()}
                        disabled={busy}
                        className="rounded-md border border-border px-3 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-70"
                      >
                        Salvar cadastro
                      </button>
                    </div>
                  </article>

                  <article className="rounded-lg border border-border bg-surface p-3">
                    <h5 className="text-sm font-semibold text-text">Consentimentos LGPD</h5>
                    <div className="mt-2 flex flex-wrap gap-3 text-sm text-text">
                      <label className="inline-flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={acceptedTermsDraft}
                          onChange={(event) => setAcceptedTermsDraft(event.currentTarget.checked)}
                        />
                        Termos aceitos
                      </label>
                      <label className="inline-flex items-center gap-2">
                        <input
                          type="checkbox"
                          checked={acceptedPrivacyDraft}
                          onChange={(event) => setAcceptedPrivacyDraft(event.currentTarget.checked)}
                        />
                        Política de privacidade aceita
                      </label>
                    </div>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <select
                        value={marketingOptInDraft === null ? "" : marketingOptInDraft ? "true" : "false"}
                        onChange={(event) => {
                          const value = event.currentTarget.value;
                          if (value === "true") {
                            setMarketingOptInDraft(true);
                            return;
                          }
                          if (value === "false") {
                            setMarketingOptInDraft(false);
                            return;
                          }
                          setMarketingOptInDraft(null);
                        }}
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      >
                        <option value="">Marketing: sem alteração</option>
                        <option value="true">Opt-in marketing</option>
                        <option value="false">Opt-out marketing</option>
                      </select>
                      <button
                        type="button"
                        onClick={() => void handleSaveConsents()}
                        disabled={busy}
                        className="rounded-md border border-border px-3 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-70"
                      >
                        Salvar consentimentos
                      </button>
                    </div>
                    <div className="mt-2">
                      <button
                        type="button"
                        onClick={() => void handleResendEmailValidation()}
                        disabled={busy}
                        className="rounded-md bg-primary px-3 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:opacity-70"
                      >
                        Reenviar validação de e-mail
                      </button>
                    </div>
                  </article>

                  <article className="rounded-lg border border-border bg-surface p-3">
                    <h5 className="text-sm font-semibold text-text">Solicitações LGPD</h5>
                    <div className="mt-2 grid gap-2 md:grid-cols-2">
                      <select
                        value={lgpdTypeDraft}
                        onChange={(event) => setLgpdTypeDraft(event.currentTarget.value as CustomerLgpdRequestType)}
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      >
                        {LGPD_REQUEST_TYPE_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <select
                        value={lgpdChannelDraft}
                        onChange={(event) =>
                          setLgpdChannelDraft(event.currentTarget.value as CustomerLgpdRequestChannel)
                        }
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      >
                        {LGPD_CHANNEL_OPTIONS.map((option) => (
                          <option key={option.value} value={option.value}>
                            {option.label}
                          </option>
                        ))}
                      </select>
                      <input
                        value={lgpdRequesterNameDraft}
                        onChange={(event) => setLgpdRequesterNameDraft(event.currentTarget.value)}
                        placeholder="Solicitante"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                      <input
                        value={lgpdRequesterEmailDraft}
                        onChange={(event) => setLgpdRequesterEmailDraft(event.currentTarget.value)}
                        placeholder="E-mail do solicitante"
                        className="rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                      />
                    </div>
                    <textarea
                      value={lgpdNotesDraft}
                      onChange={(event) => setLgpdNotesDraft(event.currentTarget.value)}
                      placeholder="Detalhes da solicitação"
                      rows={2}
                      className="mt-2 w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text"
                    />
                    <div className="mt-2 flex justify-end">
                      <button
                        type="button"
                        onClick={() => void handleCreateLgpdRequest()}
                        disabled={busy}
                        className="rounded-md border border-border px-3 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-70"
                      >
                        Criar solicitação
                      </button>
                    </div>

                    <div className="mt-3 space-y-2">
                      {lgpdRequests.map((item) => (
                        <article key={item.id} className="rounded-md border border-border bg-bg p-2">
                          <p className="text-xs font-semibold text-text">
                            {item.protocol_code} • {item.request_type}
                          </p>
                          <p className="text-xs text-muted">
                            Solicitada em {formatDateTime(item.requested_at)} • prazo {item.due_at || "-"}
                          </p>
                          <div className="mt-1 flex flex-wrap gap-1">
                            {LGPD_STATUS_OPTIONS.map((option) => (
                              <button
                                key={option.value}
                                type="button"
                                onClick={() => void handleUpdateLgpdRequestStatus(item.id, option.value)}
                                disabled={busy || item.status === option.value}
                                className="rounded border border-border px-2 py-1 text-[11px] font-semibold text-text transition hover:border-primary hover:text-primary disabled:opacity-50"
                              >
                                {option.label}
                              </button>
                            ))}
                          </div>
                        </article>
                      ))}
                      {lgpdRequests.length === 0 && (
                        <p className="text-xs text-muted">Sem solicitações LGPD para este cliente.</p>
                      )}
                    </div>
                  </article>
                </div>
              )}
            </section>
          </div>
        </>
      )}

      {(message || errorMessage) && (
        <div className="mt-4 rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          {message && <p className="text-primary">{message}</p>}
          {errorMessage && <p className="text-rose-600">{errorMessage}</p>}
        </div>
      )}
    </section>
  );
}

"use client";

import Image from "next/image";
import { type ChangeEvent, type FormEvent, useEffect, useMemo, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import { AdminSessionGate, useAdminSession } from "@/components/AdminSessionGate";
import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  fetchMyUserProfile,
  updateMeAccount,
  updateMyUserProfile,
  uploadMyUserProfileFiles,
} from "@/lib/api";
import type { UserBiometricStatus, UserDocumentType, UserProfileData } from "@/types/api";

const INPUT_CLASS =
  "w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition focus:border-primary";

const TEXTAREA_CLASS =
  "min-h-20 w-full rounded-md border border-border bg-bg px-3 py-2 text-sm text-text outline-none transition focus:border-primary";

const DOCUMENT_TYPE_OPTIONS: Array<{ value: UserDocumentType; label: string }> = [
  { value: "", label: "Nao informado" },
  { value: "CPF", label: "CPF" },
  { value: "CNPJ", label: "CNPJ" },
  { value: "RG", label: "RG" },
  { value: "CNH", label: "CNH" },
  { value: "PASSAPORTE", label: "Passaporte" },
  { value: "OUTRO", label: "Outro" },
];

type CepLookupStatus = "idle" | "loading" | "found" | "not_found" | "error";

type ProfileFormState = {
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  full_name: string;
  preferred_name: string;
  phone: string;
  phone_is_whatsapp: boolean;
  secondary_phone: string;
  birth_date: string;
  cpf: string;
  cnpj: string;
  rg: string;
  occupation: string;
  postal_code: string;
  street: string;
  street_number: string;
  address_complement: string;
  neighborhood: string;
  city: string;
  state: string;
  country: string;
  document_type: UserDocumentType;
  document_number: string;
  document_issuer: string;
  notes: string;
};

type ProfileFileState = {
  profile_photo: File | null;
  document_front_image: File | null;
  document_back_image: File | null;
  document_selfie_image: File | null;
  biometric_photo: File | null;
};

function resolveErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Falha inesperada. Tente novamente.";
}

function digitsOnly(value: string): string {
  return value.replace(/\D/g, "");
}

type CepLookupData = {
  postal_code: string;
  street: string;
  neighborhood: string;
  city: string;
  state: string;
};

async function lookupCep(cep: string): Promise<CepLookupData | null> {
  const normalized = digitsOnly(cep);
  if (normalized.length !== 8) {
    return null;
  }

  const response = await fetch(`/api/runtime/lookup-cep?cep=${encodeURIComponent(normalized)}`, {
    method: "GET",
    cache: "no-store",
  });

  if (response.status === 404) {
    return null;
  }

  if (!response.ok) {
    throw new Error("Falha ao consultar CEP.");
  }

  const payload = (await response.json()) as Record<string, string>;
  const payloadPostalCode = digitsOnly(String(payload.postal_code || normalized));
  return {
    postal_code: payloadPostalCode || normalized,
    street: String(payload.street || "").trim(),
    neighborhood: String(payload.neighborhood || "").trim(),
    city: String(payload.city || "").trim(),
    state: String(payload.state || "").trim().toUpperCase(),
  };
}

function resolveBiometricTone(status: UserBiometricStatus): StatusTone {
  if (status === "VERIFIED") {
    return "success";
  }

  if (status === "PENDING_REVIEW") {
    return "warning";
  }

  if (status === "REJECTED") {
    return "danger";
  }

  return "neutral";
}

function resolveBiometricLabel(status: UserBiometricStatus): string {
  if (status === "VERIFIED") {
    return "Biometria validada";
  }

  if (status === "PENDING_REVIEW") {
    return "Aguardando validacao";
  }

  if (status === "REJECTED") {
    return "Biometria rejeitada";
  }

  return "Biometria nao configurada";
}

function mapProfileToForm(profile: UserProfileData): ProfileFormState {
  return {
    username: "",
    email: "",
    first_name: "",
    last_name: "",
    full_name: profile.full_name ?? "",
    preferred_name: profile.preferred_name ?? "",
    phone: profile.phone ?? "",
    phone_is_whatsapp: Boolean(profile.phone_is_whatsapp),
    secondary_phone: profile.secondary_phone ?? "",
    birth_date: profile.birth_date ?? "",
    cpf: profile.cpf ?? "",
    cnpj: profile.cnpj ?? "",
    rg: profile.rg ?? "",
    occupation: profile.occupation ?? "",
    postal_code: profile.postal_code ?? "",
    street: profile.street ?? "",
    street_number: profile.street_number ?? "",
    address_complement: profile.address_complement ?? "",
    neighborhood: profile.neighborhood ?? "",
    city: profile.city ?? "",
    state: profile.state ?? "",
    country: profile.country ?? "",
    document_type: profile.document_type ?? "",
    document_number: profile.document_number ?? "",
    document_issuer: profile.document_issuer ?? "",
    notes: profile.notes ?? "",
  };
}

function createEmptyFiles(): ProfileFileState {
  return {
    profile_photo: null,
    document_front_image: null,
    document_back_image: null,
    document_selfie_image: null,
    biometric_photo: null,
  };
}

function ProfilePageContent() {
  const { user, onLogout } = useAdminSession();
  const { template } = useAdminTemplate();
  const isStyledTemplate = template === "admin-adminkit" || template === "admin-admindek";

  const [loading, setLoading] = useState(true);
  const [savingProfile, setSavingProfile] = useState(false);
  const [uploadingFiles, setUploadingFiles] = useState(false);
  const [profile, setProfile] = useState<UserProfileData | null>(null);
  const [formState, setFormState] = useState<ProfileFormState | null>(null);
  const [fileState, setFileState] = useState<ProfileFileState>(createEmptyFiles);
  const [message, setMessage] = useState("");
  const [errorMessage, setErrorMessage] = useState("");
  const [cepLookupStatus, setCepLookupStatus] = useState<CepLookupStatus>("idle");
  const [cepLookupDetail, setCepLookupDetail] = useState<string>("");
  const [lastLookupCep, setLastLookupCep] = useState<string>("");

  useEffect(() => {
    let mounted = true;

    async function loadProfile() {
      try {
        const payload = await fetchMyUserProfile();
        if (!mounted) {
          return;
        }
        setProfile(payload);
        setFormState({
          ...mapProfileToForm(payload),
          username: user.username || "",
          email: user.email || "",
          first_name: user.first_name || "",
          last_name: user.last_name || "",
        });
      } catch (error) {
        if (!mounted) {
          return;
        }
        setErrorMessage(resolveErrorMessage(error));
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    }

    void loadProfile();
    return () => {
      mounted = false;
    };
  }, [user.email, user.first_name, user.last_name, user.username]);

  const cepDigits = useMemo(
    () => digitsOnly(formState?.postal_code ?? ""),
    [formState?.postal_code],
  );

  useEffect(() => {
    let active = true;

    if (!formState) {
      return () => {
        active = false;
      };
    }

    if (cepDigits.length === 0) {
      setCepLookupStatus("idle");
      setCepLookupDetail("");
      setLastLookupCep("");
      return () => {
        active = false;
      };
    }

    if (cepDigits.length < 8) {
      setCepLookupStatus("idle");
      setCepLookupDetail("Informe os 8 digitos do CEP.");
      return () => {
        active = false;
      };
    }

    if (cepDigits === lastLookupCep) {
      return () => {
        active = false;
      };
    }

    const timer = window.setTimeout(() => {
      void (async () => {
        setCepLookupStatus("loading");
        setCepLookupDetail("Consultando CEP...");

        try {
          const result = await lookupCep(cepDigits);
          if (!active) {
            return;
          }

          if (!result) {
            setCepLookupStatus("not_found");
            setCepLookupDetail("CEP nao encontrado.");
            setLastLookupCep(cepDigits);
            return;
          }

          setCepLookupStatus("found");
          setCepLookupDetail("CEP encontrado e endereco carregado.");
          setLastLookupCep(cepDigits);

          setFormState((current) => {
            if (!current) {
              return current;
            }
            return {
              ...current,
              postal_code: result.postal_code,
              street: result.street || current.street,
              neighborhood: result.neighborhood || current.neighborhood,
              city: result.city || current.city,
              state: result.state || current.state,
            };
          });
        } catch {
          if (!active) {
            return;
          }
          setCepLookupStatus("error");
          setCepLookupDetail("Erro ao consultar CEP. Tente novamente.");
          setLastLookupCep("");
        }
      })();
    }, 420);

    return () => {
      active = false;
      window.clearTimeout(timer);
    };
  }, [cepDigits, formState, lastLookupCep]);

  function handleFieldChange<K extends keyof ProfileFormState>(
    key: K,
    value: ProfileFormState[K],
  ) {
    setFormState((current) => {
      if (!current) {
        return current;
      }
      return { ...current, [key]: value };
    });
  }

  function handleFileChange(key: keyof ProfileFileState, event: ChangeEvent<HTMLInputElement>) {
    const file = event.currentTarget.files?.[0] ?? null;
    setFileState((current) => ({ ...current, [key]: file }));
  }

  async function handleSaveProfile(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const form = event.currentTarget;
    if (!form.checkValidity()) {
      form.reportValidity();
      return;
    }

    if (!formState) {
      return;
    }

    setSavingProfile(true);
    setMessage("");
    setErrorMessage("");

    try {
      const accountPayload = await updateMeAccount({
        username: formState.username,
        email: formState.email,
        first_name: formState.first_name,
        last_name: formState.last_name,
      });
      const payload = await updateMyUserProfile({
        full_name: formState.full_name,
        preferred_name: formState.preferred_name,
        phone: formState.phone,
        phone_is_whatsapp: formState.phone_is_whatsapp,
        secondary_phone: formState.secondary_phone,
        birth_date: formState.birth_date,
        cpf: formState.cpf,
        cnpj: formState.cnpj,
        rg: formState.rg,
        occupation: formState.occupation,
        postal_code: formState.postal_code,
        street: formState.street,
        street_number: formState.street_number,
        address_complement: formState.address_complement,
        neighborhood: formState.neighborhood,
        city: formState.city,
        state: formState.state,
        country: formState.country,
        document_type: formState.document_type,
        document_number: formState.document_number,
        document_issuer: formState.document_issuer,
        notes: formState.notes,
      });
      setProfile(payload);
      setFormState({
        ...mapProfileToForm(payload),
        username: accountPayload.username || "",
        email: accountPayload.email || "",
        first_name: accountPayload.first_name || "",
        last_name: accountPayload.last_name || "",
      });
      setMessage("Dados do perfil atualizados com sucesso.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setSavingProfile(false);
    }
  }

  async function handleUploadFiles() {
    const formData = new FormData();
    if (fileState.profile_photo) {
      formData.append("profile_photo", fileState.profile_photo);
    }
    if (fileState.document_front_image) {
      formData.append("document_front_image", fileState.document_front_image);
    }
    if (fileState.document_back_image) {
      formData.append("document_back_image", fileState.document_back_image);
    }
    if (fileState.document_selfie_image) {
      formData.append("document_selfie_image", fileState.document_selfie_image);
    }
    if (fileState.biometric_photo) {
      formData.append("biometric_photo", fileState.biometric_photo);
    }

    if (Array.from(formData.keys()).length === 0) {
      setErrorMessage("Selecione ao menos um arquivo para enviar.");
      return;
    }

    setUploadingFiles(true);
    setMessage("");
    setErrorMessage("");
    try {
      const payload = await uploadMyUserProfileFiles(formData);
      setProfile(payload);
      setFormState((current) => ({
        ...mapProfileToForm(payload),
        username: current?.username ?? user.username ?? "",
        email: current?.email ?? user.email ?? "",
        first_name: current?.first_name ?? user.first_name ?? "",
        last_name: current?.last_name ?? user.last_name ?? "",
      }));
      setFileState(createEmptyFiles());
      setMessage("Arquivos enviados e vinculados ao perfil.");
    } catch (error) {
      setErrorMessage(resolveErrorMessage(error));
    } finally {
      setUploadingFiles(false);
    }
  }

  if (loading) {
    return (
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <InlinePreloader
          message="Carregando dados completos do usuario..."
          className="justify-start bg-surface/70"
        />
      </section>
    );
  }

  if (!profile || !formState) {
    return (
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <p className="text-sm text-rose-700">{errorMessage || "Nao foi possivel carregar o perfil."}</p>
      </section>
    );
  }

  return (
    <div className="space-y-6">
      <section
        className={[
          "rounded-2xl border border-border bg-surface/80 p-6 shadow-sm",
          isStyledTemplate ? "bg-white/90 dark:bg-surface/90" : "",
        ].join(" ")}
      >
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
              Area do usuario logado
            </p>
            <h1 className="mt-1 text-2xl font-bold text-text">Meu Perfil e Autenticacao</h1>
            <p className="mt-2 text-sm text-muted">
              Gerencie dados completos, endereco, documentos e biometria facial.
            </p>
          </div>
          <div className="flex flex-wrap items-center gap-2">
            <StatusPill tone="info">{user.username}</StatusPill>
            <StatusPill tone={resolveBiometricTone(profile.biometric_status)}>
              {resolveBiometricLabel(profile.biometric_status)}
            </StatusPill>
            <button
              type="button"
              onClick={onLogout}
              className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            >
              Fazer logoff
            </button>
          </div>
        </div>
      </section>

      <form
        onSubmit={handleSaveProfile}
        className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
      >
        <h2 className="text-lg font-semibold text-text">Dados adicionais completos</h2>
        <div className="mt-4 grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-sm text-muted">
            Usuario
            <input
              name="username"
              className={INPUT_CLASS}
              value={formState.username}
              onChange={(event) => handleFieldChange("username", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            E-mail
            <input
              name="email"
              type="email"
              className={INPUT_CLASS}
              value={formState.email}
              onChange={(event) => handleFieldChange("email", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Nome
            <input
              name="first_name"
              className={INPUT_CLASS}
              value={formState.first_name}
              onChange={(event) => handleFieldChange("first_name", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Sobrenome
            <input
              name="last_name"
              className={INPUT_CLASS}
              value={formState.last_name}
              onChange={(event) => handleFieldChange("last_name", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Nome completo
            <input
              name="full_name"
              className={INPUT_CLASS}
              value={formState.full_name}
              onChange={(event) => handleFieldChange("full_name", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Nome preferido
            <input
              name="preferred_name"
              className={INPUT_CLASS}
              value={formState.preferred_name}
              onChange={(event) => handleFieldChange("preferred_name", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Telefone principal
            <input
              name="phone"
              className={INPUT_CLASS}
              value={formState.phone}
              onChange={(event) => handleFieldChange("phone", event.currentTarget.value)}
            />
            <span className="inline-flex items-center gap-2 text-xs text-muted">
              <input
                name="phone_is_whatsapp"
                type="checkbox"
                checked={formState.phone_is_whatsapp}
                onChange={(event) =>
                  handleFieldChange("phone_is_whatsapp", event.currentTarget.checked)
                }
              />
              Este telefone tambem e WhatsApp (opcional)
            </span>
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Telefone secundario
            <input
              name="secondary_phone"
              className={INPUT_CLASS}
              value={formState.secondary_phone}
              onChange={(event) => handleFieldChange("secondary_phone", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Data de nascimento
            <input
              name="birth_date"
              type="date"
              className={INPUT_CLASS}
              value={formState.birth_date}
              onChange={(event) => handleFieldChange("birth_date", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Profissao/funcao
            <input
              name="occupation"
              className={INPUT_CLASS}
              value={formState.occupation}
              onChange={(event) => handleFieldChange("occupation", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            CPF
            <input
              name="cpf"
              className={INPUT_CLASS}
              value={formState.cpf}
              onChange={(event) => handleFieldChange("cpf", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            CNPJ
            <input
              name="cnpj"
              className={INPUT_CLASS}
              value={formState.cnpj}
              onChange={(event) => handleFieldChange("cnpj", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            RG
            <input
              name="rg"
              className={INPUT_CLASS}
              value={formState.rg}
              onChange={(event) => handleFieldChange("rg", event.currentTarget.value)}
            />
          </label>
        </div>

        <h3 className="mt-6 text-base font-semibold text-text">Endereco</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-sm text-muted">
            CEP
            <input
              name="postal_code"
              className={INPUT_CLASS}
              value={formState.postal_code}
              onChange={(event) => handleFieldChange("postal_code", event.currentTarget.value)}
            />
            {cepLookupDetail && (
              <span
                className={[
                  "text-xs",
                  cepLookupStatus === "found"
                    ? "text-emerald-600"
                    : cepLookupStatus === "error" || cepLookupStatus === "not_found"
                      ? "text-rose-600"
                      : "text-muted",
                ].join(" ")}
              >
                {cepLookupDetail}
              </span>
            )}
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Rua
            <input
              name="street"
              className={INPUT_CLASS}
              value={formState.street}
              onChange={(event) => handleFieldChange("street", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Numero
            <input
              name="street_number"
              className={INPUT_CLASS}
              value={formState.street_number}
              onChange={(event) => handleFieldChange("street_number", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Complemento
            <input
              name="address_complement"
              className={INPUT_CLASS}
              value={formState.address_complement}
              onChange={(event) =>
                handleFieldChange("address_complement", event.currentTarget.value)
              }
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Bairro
            <input
              name="neighborhood"
              className={INPUT_CLASS}
              value={formState.neighborhood}
              onChange={(event) => handleFieldChange("neighborhood", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Cidade
            <input
              name="city"
              className={INPUT_CLASS}
              value={formState.city}
              onChange={(event) => handleFieldChange("city", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Estado
            <input
              name="state"
              className={INPUT_CLASS}
              value={formState.state}
              onChange={(event) => handleFieldChange("state", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Pais
            <input
              name="country"
              className={INPUT_CLASS}
              value={formState.country}
              onChange={(event) => handleFieldChange("country", event.currentTarget.value)}
            />
          </label>
        </div>

        <h3 className="mt-6 text-base font-semibold text-text">Documentos</h3>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          <label className="grid gap-1 text-sm text-muted">
            Tipo do documento
            <select
              name="document_type"
              className={INPUT_CLASS}
              value={formState.document_type}
              onChange={(event) =>
                handleFieldChange("document_type", event.currentTarget.value as UserDocumentType)
              }
            >
              {DOCUMENT_TYPE_OPTIONS.map((option) => (
                <option key={option.value || "empty"} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Numero do documento
            <input
              name="document_number"
              className={INPUT_CLASS}
              value={formState.document_number}
              onChange={(event) => handleFieldChange("document_number", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Orgao emissor
            <input
              name="document_issuer"
              className={INPUT_CLASS}
              value={formState.document_issuer}
              onChange={(event) => handleFieldChange("document_issuer", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted md:col-span-2">
            Observacoes
            <textarea
              name="notes"
              className={TEXTAREA_CLASS}
              value={formState.notes}
              onChange={(event) => handleFieldChange("notes", event.currentTarget.value)}
            />
          </label>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="submit"
            disabled={savingProfile}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {savingProfile ? "Salvando..." : "Salvar dados do perfil"}
          </button>
        </div>
      </form>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-text">Fotos, digitalizacao e biometria</h2>
        <p className="mt-1 text-sm text-muted">
          Use upload tradicional ou camera do dispositivo para digitalizar documentos e cadastrar
          biometria por foto.
        </p>

        <div className="mt-4 grid gap-4 lg:grid-cols-3">
          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-sm font-semibold text-text">Foto de perfil</p>
            <input
              name="profile_photo"
              type="file"
              accept="image/*"
              className="mt-3 block w-full text-sm text-muted"
              onChange={(event) => handleFileChange("profile_photo", event)}
            />
            {profile.profile_photo_url && (
              <Image
                src={profile.profile_photo_url}
                alt="Foto de perfil atual"
                width={220}
                height={220}
                unoptimized
                className="mt-3 rounded-lg border border-border object-cover"
              />
            )}
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-sm font-semibold text-text">Documentos (frente/verso/selfie)</p>
            <div className="mt-3 grid gap-2">
              <input
                name="document_front_image"
                type="file"
                accept="image/*"
                className="block w-full text-sm text-muted"
                onChange={(event) => handleFileChange("document_front_image", event)}
              />
              <input
                name="document_back_image"
                type="file"
                accept="image/*"
                className="block w-full text-sm text-muted"
                onChange={(event) => handleFileChange("document_back_image", event)}
              />
              <input
                name="document_selfie_image"
                type="file"
                accept="image/*"
                className="block w-full text-sm text-muted"
                onChange={(event) => handleFileChange("document_selfie_image", event)}
              />
            </div>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-sm font-semibold text-text">Biometria facial (foto)</p>
            <input
              name="biometric_photo"
              type="file"
              accept="image/*"
              className="mt-3 block w-full text-sm text-muted"
              onChange={(event) => handleFileChange("biometric_photo", event)}
            />
            <p className="mt-2 text-xs text-muted">
              Status atual: {resolveBiometricLabel(profile.biometric_status)}.
            </p>
            {profile.biometric_photo_url && (
              <Image
                src={profile.biometric_photo_url}
                alt="Biometria atual"
                width={220}
                height={220}
                unoptimized
                className="mt-3 rounded-lg border border-border object-cover"
              />
            )}
          </article>
        </div>

        <div className="mt-5 flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={handleUploadFiles}
            disabled={uploadingFiles}
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90 disabled:cursor-not-allowed disabled:opacity-70"
          >
            {uploadingFiles ? "Enviando arquivos..." : "Enviar fotos/documentos/biometria"}
          </button>
        </div>
      </section>

      {(message || errorMessage) && (
        <section className="rounded-xl border border-border bg-bg px-4 py-3 text-sm">
          {message && <p className="text-primary">{message}</p>}
          {errorMessage && <p className="text-rose-700">{errorMessage}</p>}
        </section>
      )}
    </div>
  );
}

export default function PerfilPage() {
  return (
    <AdminSessionGate>
      <ProfilePageContent />
    </AdminSessionGate>
  );
}

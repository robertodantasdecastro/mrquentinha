"use client";

import Image from "next/image";
import { type ChangeEvent, type FormEvent, useEffect, useState } from "react";
import { StatusPill, type StatusTone } from "@mrquentinha/ui";

import { AdminSessionGate, useAdminSession } from "@/components/AdminSessionGate";
import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { InlinePreloader } from "@/components/InlinePreloader";
import {
  ApiError,
  fetchMyUserProfile,
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

type ProfileFormState = {
  full_name: string;
  preferred_name: string;
  phone: string;
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
    full_name: profile.full_name ?? "",
    preferred_name: profile.preferred_name ?? "",
    phone: profile.phone ?? "",
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

  useEffect(() => {
    let mounted = true;

    async function loadProfile() {
      try {
        const payload = await fetchMyUserProfile();
        if (!mounted) {
          return;
        }
        setProfile(payload);
        setFormState(mapProfileToForm(payload));
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
  }, []);

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
    if (!formState) {
      return;
    }

    setSavingProfile(true);
    setMessage("");
    setErrorMessage("");

    try {
      const payload = await updateMyUserProfile(formState);
      setProfile(payload);
      setFormState(mapProfileToForm(payload));
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
      setFormState(mapProfileToForm(payload));
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
            Nome completo
            <input
              className={INPUT_CLASS}
              value={formState.full_name}
              onChange={(event) => handleFieldChange("full_name", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Nome preferido
            <input
              className={INPUT_CLASS}
              value={formState.preferred_name}
              onChange={(event) => handleFieldChange("preferred_name", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Telefone principal
            <input
              className={INPUT_CLASS}
              value={formState.phone}
              onChange={(event) => handleFieldChange("phone", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Telefone secundario
            <input
              className={INPUT_CLASS}
              value={formState.secondary_phone}
              onChange={(event) => handleFieldChange("secondary_phone", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Data de nascimento
            <input
              type="date"
              className={INPUT_CLASS}
              value={formState.birth_date}
              onChange={(event) => handleFieldChange("birth_date", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Profissao/funcao
            <input
              className={INPUT_CLASS}
              value={formState.occupation}
              onChange={(event) => handleFieldChange("occupation", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            CPF
            <input
              className={INPUT_CLASS}
              value={formState.cpf}
              onChange={(event) => handleFieldChange("cpf", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            CNPJ
            <input
              className={INPUT_CLASS}
              value={formState.cnpj}
              onChange={(event) => handleFieldChange("cnpj", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            RG
            <input
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
              className={INPUT_CLASS}
              value={formState.postal_code}
              onChange={(event) => handleFieldChange("postal_code", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Rua
            <input
              className={INPUT_CLASS}
              value={formState.street}
              onChange={(event) => handleFieldChange("street", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Numero
            <input
              className={INPUT_CLASS}
              value={formState.street_number}
              onChange={(event) => handleFieldChange("street_number", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Complemento
            <input
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
              className={INPUT_CLASS}
              value={formState.neighborhood}
              onChange={(event) => handleFieldChange("neighborhood", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Cidade
            <input
              className={INPUT_CLASS}
              value={formState.city}
              onChange={(event) => handleFieldChange("city", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Estado
            <input
              className={INPUT_CLASS}
              value={formState.state}
              onChange={(event) => handleFieldChange("state", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Pais
            <input
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
              className={INPUT_CLASS}
              value={formState.document_number}
              onChange={(event) => handleFieldChange("document_number", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted">
            Orgao emissor
            <input
              className={INPUT_CLASS}
              value={formState.document_issuer}
              onChange={(event) => handleFieldChange("document_issuer", event.currentTarget.value)}
            />
          </label>
          <label className="grid gap-1 text-sm text-muted md:col-span-2">
            Observacoes
            <textarea
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
                type="file"
                accept="image/*"
                capture="environment"
                className="block w-full text-sm text-muted"
                onChange={(event) => handleFileChange("document_front_image", event)}
              />
              <input
                type="file"
                accept="image/*"
                capture="environment"
                className="block w-full text-sm text-muted"
                onChange={(event) => handleFileChange("document_back_image", event)}
              />
              <input
                type="file"
                accept="image/*"
                capture="user"
                className="block w-full text-sm text-muted"
                onChange={(event) => handleFileChange("document_selfie_image", event)}
              />
            </div>
          </article>

          <article className="rounded-xl border border-border bg-bg p-4">
            <p className="text-sm font-semibold text-text">Biometria facial (foto)</p>
            <input
              type="file"
              accept="image/*"
              capture="user"
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

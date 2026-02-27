"use client";

import Link from "next/link";
import { useParams } from "next/navigation";

import { AdminSessionGate } from "@/components/AdminSessionGate";
import { ModulePageShell } from "@/components/ModulePageShell";
import {
  FLUXO_BASE_PATH,
  FLUXO_MENU_ITEMS,
  FluxoOperacionalSections,
  type FluxoSectionKey,
} from "@/app/modulos/fluxo-operacional/sections";
import { PROCESS_JOURNEY_STEPS } from "@/lib/processJourney";

const STEP_KEYS = PROCESS_JOURNEY_STEPS.map((step) => step.slug);

function resolveStepKey(value: string | string[] | undefined): FluxoSectionKey {
  if (Array.isArray(value)) {
    return STEP_KEYS.includes(value[0]) ? value[0] : "all";
  }

  if (!value) {
    return "all";
  }

  return STEP_KEYS.includes(value) ? value : "all";
}

export default function FluxoOperacionalStepPage() {
  const params = useParams();
  const step = resolveStepKey(params?.step);

  const currentIndex = PROCESS_JOURNEY_STEPS.findIndex((item) => item.slug === step);
  const currentStep = currentIndex >= 0 ? PROCESS_JOURNEY_STEPS[currentIndex] : null;
  const previousStep = currentIndex > 0 ? PROCESS_JOURNEY_STEPS[currentIndex - 1] : null;
  const nextStep =
    currentIndex >= 0 && currentIndex < PROCESS_JOURNEY_STEPS.length - 1
      ? PROCESS_JOURNEY_STEPS[currentIndex + 1]
      : null;

  return (
    <AdminSessionGate>
      <ModulePageShell
        title="Fluxo operacional guiado"
        description="Use a navegacao anterior/proxima para executar a rotina completa do dia sem perder contexto."
        statusLabel={currentStep ? `Etapa ${currentIndex + 1}` : "Visao geral"}
        statusTone="info"
        menuItems={FLUXO_MENU_ITEMS}
        activeKey={step}
      >
        {currentStep && (
          <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
              Etapa atual
            </p>
            <h2 className="mt-1 text-xl font-semibold text-text">{currentStep.title}</h2>
            <p className="mt-2 text-sm text-muted">{currentStep.description}</p>

            <div className="mt-4 flex flex-wrap gap-2">
              <Link
                href={currentStep.moduleHref}
                className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary/90"
              >
                {currentStep.moduleLabel}
              </Link>
              <Link
                href={FLUXO_BASE_PATH}
                className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
              >
                Voltar para visao geral
              </Link>
            </div>

            <div className="mt-4 flex flex-wrap gap-2">
              {previousStep ? (
                <Link
                  href={`${FLUXO_BASE_PATH}/${previousStep.slug}`}
                  className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
                >
                  Etapa anterior
                </Link>
              ) : (
                <span className="rounded-md border border-border bg-bg px-4 py-2 text-sm text-muted">
                  Inicio do fluxo
                </span>
              )}

              {nextStep ? (
                <Link
                  href={`${FLUXO_BASE_PATH}/${nextStep.slug}`}
                  className="rounded-md bg-status-info px-4 py-2 text-sm font-semibold text-white transition hover:opacity-90"
                >
                  Proxima etapa
                </Link>
              ) : (
                <span className="rounded-md border border-border bg-bg px-4 py-2 text-sm text-muted">
                  Fluxo concluido
                </span>
              )}
            </div>
          </section>
        )}

        <FluxoOperacionalSections activeSection={step} />
      </ModulePageShell>
    </AdminSessionGate>
  );
}

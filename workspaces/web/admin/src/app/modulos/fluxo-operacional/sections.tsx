"use client";

import Link from "next/link";
import { StatusPill } from "@mrquentinha/ui";

import {
  getJourneyStepIndex,
  PROCESS_JOURNEY_STEPS,
  type ProcessJourneyStep,
} from "@/lib/processJourney";

export const FLUXO_BASE_PATH = "/modulos/fluxo-operacional";

export const FLUXO_MENU_ITEMS = [
  { key: "all", label: "Visao geral", href: FLUXO_BASE_PATH },
  ...PROCESS_JOURNEY_STEPS.map((step) => ({
    key: step.slug,
    label: step.title,
    href: `${FLUXO_BASE_PATH}/${step.slug}`,
  })),
];

export type FluxoSectionKey = "all" | ProcessJourneyStep["slug"];

type FluxoOperacionalSectionsProps = {
  activeSection?: FluxoSectionKey;
};

function resolveStepTone(index: number, activeIndex: number): "info" | "success" | "neutral" {
  if (index < activeIndex) {
    return "success";
  }
  if (index === activeIndex) {
    return "info";
  }
  return "neutral";
}

export function FluxoOperacionalSections({
  activeSection = "all",
}: FluxoOperacionalSectionsProps) {
  const selectedIndex =
    activeSection === "all" ? 0 : Math.max(getJourneyStepIndex(activeSection), 0);

  return (
    <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <h2 className="text-lg font-semibold text-text">Execucao guiada ponta a ponta</h2>
          <p className="mt-1 text-sm text-muted">
            Navegue por cada etapa com contexto operacional e avance para a proxima acao.
          </p>
        </div>
        <StatusPill tone="info">Template orientado por jornada</StatusPill>
      </div>

      <ol className="mt-4 space-y-3">
        {PROCESS_JOURNEY_STEPS.map((step, index) => {
          const isCurrent = step.slug === activeSection;
          const tone = resolveStepTone(index, selectedIndex);

          return (
            <li
              key={step.slug}
              className={[
                "rounded-xl border bg-bg p-4 transition",
                isCurrent
                  ? "border-primary shadow-sm"
                  : "border-border hover:border-primary/50",
              ].join(" ")}
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div>
                  <p className="text-xs font-semibold uppercase tracking-[0.1em] text-muted">
                    Etapa {index + 1}
                  </p>
                  <h3 className="mt-1 text-base font-semibold text-text">{step.title}</h3>
                  <p className="mt-1 text-sm text-muted">{step.description}</p>
                </div>
                <StatusPill tone={tone}>{isCurrent ? "Atual" : "Planejado"}</StatusPill>
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                <Link
                  href={`${FLUXO_BASE_PATH}/${step.slug}`}
                  className="rounded-full border border-primary px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-primary transition hover:bg-primary/10"
                >
                  Abrir etapa guiada
                </Link>
                <Link
                  href={step.moduleHref}
                  className="rounded-full border border-border px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted transition hover:border-primary hover:text-primary"
                >
                  {step.moduleLabel}
                </Link>
              </div>
            </li>
          );
        })}
      </ol>
    </section>
  );
}

"use client";

import { AppFooter, Container } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { useSyncExternalStore } from "react";

import { useClientTemplate } from "@/components/ClientTemplateProvider";

const PORTAL_URL =
  process.env.NEXT_PUBLIC_PORTAL_URL?.trim() || "https://www.mrquentinha.com.br";
const PRIVATE_IPV4_PATTERN = /^(10\.|127\.|192\.168\.|172\.(1[6-9]|2\d|3[0-1])\.)/;

function isLocalNetworkHostname(hostname: string): boolean {
  return (
    hostname === "localhost" ||
    hostname === "0.0.0.0" ||
    hostname.endsWith(".local") ||
    PRIVATE_IPV4_PATTERN.test(hostname)
  );
}

function resolvePortalUrlForCurrentHost(fallback: string): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  if (!hostname || !isLocalNetworkHostname(hostname)) {
    return fallback;
  }

  return `${protocol}//${hostname}:3000`;
}

function subscribeNoop(): () => void {
  return () => {};
}

function useRuntimePortalUrl(fallback: string): string {
  return useSyncExternalStore(
    subscribeNoop,
    () => resolvePortalUrlForCurrentHost(fallback),
    () => fallback,
  );
}

export function Footer() {
  const { template } = useClientTemplate();
  const isQuentinhasTemplate = template === "client-quentinhas";
  const isVitrineTemplate = template === "client-vitrine-fit";
  const isEditorialTemplate = template === "client-editorial-jp";
  const portalUrl = useRuntimePortalUrl(PORTAL_URL);
  const currentYear = new Date().getFullYear();

  return (
    <AppFooter
      className={
        isVitrineTemplate
          ? "border-t border-primary/30 bg-gradient-to-r from-bg via-surface/70 to-bg"
          : isEditorialTemplate
            ? "border-t border-primary/25 bg-gradient-to-r from-surface/60 via-bg to-surface/60"
          : isQuentinhasTemplate
            ? "border-t-2 border-primary/30 bg-surface/70"
            : "bg-bg/80"
      }
    >
      <Container className="flex flex-wrap items-center justify-between gap-4 py-4 text-xs text-muted">
        <div className="inline-flex items-center gap-3">
          <span className="inline-flex rounded-md bg-white/95 px-1.5 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
            <Image
              src="/brand/original_png/icon_app_original.png"
              alt="Mr Quentinha"
              width={28}
              height={26}
            />
          </span>
          <p className="text-sm font-semibold text-text">Mr Quentinha Web Cliente</p>
        </div>
        <div className="flex flex-wrap items-center gap-3">
          <Link className="transition hover:text-primary" href="/privacidade">
            Privacidade
          </Link>
          <Link className="transition hover:text-primary" href="/termos">
            Termos de uso
          </Link>
          <Link className="transition hover:text-primary" href="/lgpd">
            LGPD
          </Link>
          <Link className="transition hover:text-primary" href="/suporte">
            Suporte
          </Link>
          <Link className="transition hover:text-primary" href="/wiki">
            Wiki
          </Link>
          <a className="transition hover:text-primary" href={portalUrl} target="_blank" rel="noreferrer">
            Portal institucional
          </a>
          <span>© {currentYear} Mr Quentinha. Todos os direitos reservados.</span>
        </div>
        <p className="max-w-md text-right">
          {isVitrineTemplate
            ? "Vitrine Fit: fotos grandes, descoberta rapida e checkout direto."
            : isEditorialTemplate
            ? "Editorial JP: blocos visuais amplos, curadoria e conversao no app."
            : isQuentinhasTemplate
            ? "Linha Quentinhas: pedido rapido, acompanhamento e confirmacao."
            : "Fluxo de checkout e pedidos em evolucao continua."}
        </p>
      </Container>
    </AppFooter>
  );
}

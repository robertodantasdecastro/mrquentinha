"use client";

import { AppFooter, Container } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { useSyncExternalStore } from "react";

import { isLocalNetworkHostname } from "@/lib/networkHost";
import { useTemplate } from "./TemplateProvider";

const ADMIN_URL =
  process.env.NEXT_PUBLIC_ADMIN_URL?.trim() || "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

function resolveUrlForCurrentHost(port: number, fallback: string): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  if (!hostname || !isLocalNetworkHostname(hostname)) {
    return fallback;
  }

  return `${protocol}//${hostname}:${port}`;
}

function subscribeNoop(): () => void {
  return () => {};
}

function useRuntimeUrl(port: number, fallback: string): string {
  return useSyncExternalStore(
    subscribeNoop,
    () => resolveUrlForCurrentHost(port, fallback),
    () => fallback,
  );
}

export function Footer() {
  const { template } = useTemplate();
  const isEditorial = template === "editorial-jp";
  const adminUrl = useRuntimeUrl(3002, ADMIN_URL);
  const clientAreaUrl = useRuntimeUrl(3001, CLIENT_AREA_URL);
  const currentYear = new Date().getFullYear();

  return (
    <AppFooter
      className={
        isEditorial
          ? "border-t border-primary/25 bg-gradient-to-r from-surface/70 via-bg to-surface/70"
          : ""
      }
    >
      <Container className="flex w-full flex-col gap-6 py-10 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="inline-flex rounded-lg bg-white/95 px-2 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
            <Image
              src="/brand/original_png/logo_wordmark_original.png"
              alt="Mr Quentinha"
              width={176}
              height={67}
            />
          </div>
          <p className="mt-2 text-sm text-muted">
            Marmitas com cardapio diario, planejamento de estoque e gestao completa.
          </p>
        </div>

        <div className="flex flex-col gap-4 text-sm font-medium text-muted">
          <div className="flex flex-wrap items-center gap-3">
            <Link className="transition hover:text-primary" href="/">
              Home
            </Link>
            <Link className="transition hover:text-primary" href="/cardapio">
              Cardapio
            </Link>
            <Link className="transition hover:text-primary" href="/app">
              Vendas (App)
            </Link>
            <Link className="transition hover:text-primary" href="/suporte">
              Suporte
            </Link>
            <Link className="transition hover:text-primary" href="/wiki">
              Wiki
            </Link>
            <Link className="transition hover:text-primary" href="/contato">
              Contato
            </Link>
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
          </div>
          <div className="flex flex-wrap items-center gap-3 text-xs text-muted">
            <a className="transition hover:text-primary" href={adminUrl} target="_blank" rel="noreferrer">
              Gestao
            </a>
            <a className="transition hover:text-primary" href={clientAreaUrl} target="_blank" rel="noreferrer">
              Area de vendas (App)
            </a>
            <span>© {currentYear} Mr Quentinha. Todos os direitos reservados.</span>
          </div>
        </div>
      </Container>
    </AppFooter>
  );
}

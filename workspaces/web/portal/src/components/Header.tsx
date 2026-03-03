"use client";

import { Container, Navbar, ThemeToggle } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { useState, useSyncExternalStore } from "react";

import { isLocalNetworkHostname } from "@/lib/networkHost";

import { useTemplate } from "./TemplateProvider";

const ADMIN_URL =
  process.env.NEXT_PUBLIC_ADMIN_URL?.trim() || "https://admin.mrquentinha.com.br";
const CLIENT_AREA_FALLBACK =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

function resolveUrlForCurrentHost(port: number, fallback: string): string {
  if (typeof window === "undefined") {
    return fallback;
  }

  const hostname = window.location.hostname;
  const protocol = window.location.protocol;
  if (!hostname) {
    return fallback;
  }

  if (!isLocalNetworkHostname(hostname)) {
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

const NAV_LINKS_CLASSIC = [
  { href: "/", label: "Home" },
  { href: "/cardapio", label: "Cardapio" },
  { href: "/app", label: "Vendas (App)" },
  { href: "/suporte", label: "Suporte" },
  { href: "/wiki", label: "Wiki" },
  { href: "/contato", label: "Contato" },
];

const NAV_LINKS_LETSFIT = [
  ...NAV_LINKS_CLASSIC,
  { href: "/sobre", label: "Sobre o kit" },
  { href: "/como-funciona", label: "Como Funciona" },
];

export function Header() {
  const { template } = useTemplate();
  const isLetsFit = template === "letsfit-clean";
  const isEditorial = template === "editorial-jp";
  const NAV_LINKS = isLetsFit || isEditorial ? NAV_LINKS_LETSFIT : NAV_LINKS_CLASSIC;
  const adminUrl = useRuntimeUrl(3002, ADMIN_URL);
  const clientAreaUrl = useRuntimeUrl(3001, CLIENT_AREA_FALLBACK);
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <Navbar
      className={
        isEditorial
          ? "border-b border-primary/20 bg-gradient-to-r from-bg via-surface/85 to-bg"
          : ""
      }
    >
      <Container className="pt-3">
        <div className="flex items-center justify-between gap-3">
          <Link href="/" className="flex items-center gap-3" aria-label="Mr Quentinha">
            <span className="inline-flex rounded-lg bg-white/95 px-2 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
              <Image
                src="/brand/original_png/logo_wordmark_original.png"
                alt="Mr Quentinha"
                width={184}
                height={71}
                priority
              />
            </span>
          </Link>

          <div className="flex items-center gap-2">
            {!isLetsFit && (
              <a
                className="hidden rounded-md border border-border bg-surface px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted transition hover:border-primary hover:text-primary sm:inline-flex"
                href={adminUrl}
                target="_blank"
                rel="noreferrer"
              >
                Gestao
              </a>
            )}
            <a
              className="hidden rounded-md bg-primary px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:bg-primary-soft sm:inline-flex"
              href={clientAreaUrl}
              target="_blank"
              rel="noreferrer"
            >
              Area do Cliente
            </a>
            <ThemeToggle storageKey="mrq-theme" />
            <button
              type="button"
              className="inline-flex h-10 w-10 items-center justify-center rounded-md border border-border bg-bg text-text transition hover:border-primary hover:text-primary md:hidden"
              onClick={() => setMenuOpen((current) => !current)}
              aria-expanded={menuOpen}
              aria-label={menuOpen ? "Fechar menu" : "Abrir menu"}
            >
              {menuOpen ? "×" : "≡"}
            </button>
          </div>
        </div>

        <nav
          className={[
            "mt-3 pb-3 text-sm font-medium text-muted",
            menuOpen ? "block" : "hidden md:block",
          ].join(" ")}
        >
          <div
            className={[
              "scrollbar-none flex items-center gap-2 overflow-x-auto",
              isLetsFit
                ? "md:justify-center md:gap-8"
                : isEditorial
                  ? "md:justify-center md:gap-6 md:text-sm md:uppercase md:tracking-[0.08em] text-xs"
                  : "md:gap-5",
            ].join(" ")}
          >
            {NAV_LINKS.map((link) => (
              <Link
                key={link.href}
                className={`rounded-md border border-transparent px-3 py-2 whitespace-nowrap transition hover:border-primary/40 hover:text-primary ${isEditorial ? "font-semibold" : ""}`}
                href={link.href}
                onClick={() => setMenuOpen(false)}
              >
                {link.label}
              </Link>
            ))}
          </div>

          <div className="mt-3 grid gap-2 md:hidden">
            {!isLetsFit && (
              <a
                className="rounded-md border border-border bg-surface px-3 py-2 text-center text-xs font-semibold uppercase tracking-wide text-muted transition hover:border-primary hover:text-primary"
                href={adminUrl}
                target="_blank"
                rel="noreferrer"
                onClick={() => setMenuOpen(false)}
              >
                Gestao
              </a>
            )}
            <a
              className="rounded-md bg-primary px-3 py-2 text-center text-xs font-semibold uppercase tracking-wide text-white transition hover:bg-primary-soft"
              href={clientAreaUrl}
              target="_blank"
              rel="noreferrer"
              onClick={() => setMenuOpen(false)}
            >
              Area do Cliente
            </a>
          </div>
        </nav>
      </Container>
    </Navbar>
  );
}

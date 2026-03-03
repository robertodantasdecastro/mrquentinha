"use client";

import { Container, Navbar, ThemeToggle } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

import { useClientTemplate } from "@/components/ClientTemplateProvider";

const NAV_ITEMS = [
  { href: "/", label: "Cardapio" },
  { href: "/pedidos", label: "Meus pedidos" },
  { href: "/suporte", label: "Suporte" },
  { href: "/wiki", label: "Wiki" },
  { href: "/conta", label: "Conta" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/" || pathname === "/cardapio";
  }

  return pathname.startsWith(href);
}

export function Header() {
  const pathname = usePathname();
  const { template } = useClientTemplate();
  const isQuentinhasTemplate = template === "client-quentinhas";
  const isVitrineTemplate = template === "client-vitrine-fit";
  const isEditorialTemplate = template === "client-editorial-jp";
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <Navbar
      className={
        isVitrineTemplate
          ? "border-b border-primary/30 bg-gradient-to-r from-bg via-surface to-bg"
          : isEditorialTemplate
            ? "border-b border-primary/25 bg-gradient-to-r from-bg via-surface/85 to-bg"
          : isQuentinhasTemplate
            ? "border-b-2 border-primary/40 bg-bg/90"
            : ""
      }
    >
      <Container className="flex items-center justify-between gap-3 py-3">
        <Link href="/" aria-label="Mr Quentinha" className="shrink-0">
          <span className="inline-flex rounded-lg bg-white/95 px-2 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
            <Image
              src="/brand/original_png/logo_wordmark_original.png"
              alt="Mr Quentinha"
              width={164}
              height={63}
              priority
            />
          </span>
        </Link>

        <div className="flex items-center gap-2">
          <ThemeToggle storageKey="mrq-client-theme" />
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
      </Container>

      <Container className={menuOpen ? "block pb-3 md:hidden" : "hidden pb-3 md:hidden"}>
        <nav
          className={[
            "grid gap-2 rounded-xl border border-border bg-surface p-2 text-xs font-semibold uppercase tracking-[0.08em]",
            isVitrineTemplate
              ? "bg-white/80 shadow-sm dark:bg-bg/70"
              : isEditorialTemplate
                ? "bg-bg/90"
                : "",
          ].join(" ")}
        >
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);
            return (
              <Link
                key={`mobile:${item.href}`}
                href={item.href}
                onClick={() => setMenuOpen(false)}
                className={[
                  "rounded-md px-3 py-2 transition",
                  active ? "bg-primary text-white" : "text-muted hover:bg-bg hover:text-text",
                ].join(" ")}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </Container>

      <Container className="hidden pb-3 md:block">
        <nav
          className={[
            "scrollbar-none flex max-w-[calc(100vw-170px)] items-center gap-1 overflow-x-auto p-1 text-xs font-semibold uppercase tracking-[0.08em] md:max-w-none md:text-sm",
            isVitrineTemplate
              ? "rounded-xl border border-border/80 bg-white/70 shadow-sm dark:bg-bg/60"
              : isEditorialTemplate
                ? "rounded-lg border border-border bg-bg/85 shadow-sm"
                : "",
            isQuentinhasTemplate
              ? "rounded-md border border-border bg-bg"
              : "rounded-full border border-border bg-surface",
          ].join(" ")}
        >
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMenuOpen(false)}
                className={[
                  isQuentinhasTemplate || isVitrineTemplate || isEditorialTemplate
                    ? "rounded-md px-3 py-2 transition"
                    : "rounded-full px-3 py-2 transition",
                  active
                    ? "bg-primary text-white"
                    : "text-muted hover:bg-bg hover:text-text",
                ].join(" ")}
              >
                {item.label}
              </Link>
            );
          })}
        </nav>
      </Container>
    </Navbar>
  );
}

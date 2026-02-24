"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

type Theme = "light" | "dark";

const ADMIN_URL = "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL = "https://app.mrquentinha.com.br";

function resolveThemeFromBrowser(): Theme {
  if (typeof window === "undefined") {
    return "light";
  }

  const storedTheme = localStorage.getItem("mrq-theme");
  if (storedTheme === "light" || storedTheme === "dark") {
    return storedTheme;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

function getInitialTheme(): Theme {
  if (typeof document === "undefined") {
    return "light";
  }

  const attrTheme = document.documentElement.getAttribute("data-theme");
  if (attrTheme === "light" || attrTheme === "dark") {
    return attrTheme;
  }

  return resolveThemeFromBrowser();
}

function applyTheme(theme: Theme) {
  document.documentElement.setAttribute("data-theme", theme);
  localStorage.setItem("mrq-theme", theme);
}

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/cardapio", label: "Cardapio" },
  { href: "/app", label: "App" },
  { href: "/contato", label: "Contato" },
];

export function Header() {
  const [theme, setTheme] = useState<Theme>(getInitialTheme);

  useEffect(() => {
    applyTheme(theme);
  }, [theme]);

  const toggleTheme = () => {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  };

  return (
    <header className="sticky top-0 z-40 border-b border-border/80 bg-bg/95 backdrop-blur">
      <div className="mx-auto w-full max-w-6xl px-4 pt-3 md:px-6">
        <div className="flex items-center justify-between gap-3">
          <Link href="/" className="flex items-center gap-3" aria-label="Mr Quentinha">
            <Image src="/brand/logo_wordmark.svg" alt="Mr Quentinha" width={164} height={42} priority />
          </Link>

          <div className="flex items-center gap-2">
            <a
              className="hidden rounded-md border border-border bg-surface px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted transition hover:border-primary hover:text-primary sm:inline-flex"
              href={ADMIN_URL}
              target="_blank"
              rel="noreferrer"
            >
              Gestao
            </a>
            <a
              className="hidden rounded-md bg-primary px-3 py-2 text-xs font-semibold uppercase tracking-wide text-white transition hover:bg-primary-soft sm:inline-flex"
              href={CLIENT_AREA_URL}
              target="_blank"
              rel="noreferrer"
            >
              Area do Cliente
            </a>
            <button
              type="button"
              onClick={toggleTheme}
              className="rounded-md border border-border bg-surface px-3 py-2 text-xs font-semibold uppercase tracking-wide text-muted transition hover:border-primary hover:text-primary"
              aria-label="Alternar tema"
            >
              Tema
            </button>
          </div>
        </div>

        <nav className="scrollbar-none mt-3 flex items-center gap-2 overflow-x-auto pb-3 text-sm font-medium text-muted md:gap-5">
          {NAV_LINKS.map((link) => (
            <Link
              key={link.href}
              className="rounded-md border border-transparent px-3 py-2 whitespace-nowrap transition hover:border-primary/40 hover:text-primary"
              href={link.href}
            >
              {link.label}
            </Link>
          ))}
        </nav>
      </div>
    </header>
  );
}

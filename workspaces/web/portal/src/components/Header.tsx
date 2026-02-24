"use client";

import { Container, Navbar, ThemeToggle } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";

const ADMIN_URL = "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL = "https://app.mrquentinha.com.br";

const NAV_LINKS = [
  { href: "/", label: "Home" },
  { href: "/cardapio", label: "Cardapio" },
  { href: "/app", label: "App" },
  { href: "/contato", label: "Contato" },
];

export function Header() {
  return (
    <Navbar>
      <Container className="pt-3">
        <div className="flex items-center justify-between gap-3">
          <Link href="/" className="flex items-center gap-3" aria-label="Mr Quentinha">
            <Image
              src="/brand/logo_wordmark.svg"
              alt="Mr Quentinha"
              width={164}
              height={42}
              priority
            />
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
            <ThemeToggle storageKey="mrq-theme" />
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
      </Container>
    </Navbar>
  );
}

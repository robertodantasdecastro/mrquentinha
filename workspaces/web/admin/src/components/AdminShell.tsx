"use client";

import { Container, Navbar, ThemeToggle } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  { href: "/#dashboard", label: "Dashboard" },
  { href: "/#modulos", label: "Modulos" },
  { href: "/#prioridades", label: "Prioridades" },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === "/" && href === "/#dashboard";
}

export function AdminShell() {
  const pathname = usePathname();

  return (
    <Navbar>
      <Container className="flex flex-wrap items-center justify-between gap-3 py-3">
        <Link href="/" aria-label="Mr Quentinha Admin" className="shrink-0">
          <Image
            src="/brand/logo_wordmark.svg"
            alt="Mr Quentinha"
            width={154}
            height={40}
            priority
          />
        </Link>

        <nav className="flex items-center gap-1 rounded-full border border-border bg-surface p-1 text-xs font-semibold uppercase tracking-[0.08em] md:text-sm">
          {NAV_ITEMS.map((item) => {
            const active = isActive(pathname, item.href);

            return (
              <Link
                key={item.href}
                href={item.href}
                className={[
                  "rounded-full px-3 py-2 transition",
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

        <div className="flex items-center gap-3">
          <span className="rounded-full border border-border bg-surface px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
            Admin Web
          </span>
          <ThemeToggle storageKey="mrq-admin-theme" />
        </div>
      </Container>
    </Navbar>
  );
}

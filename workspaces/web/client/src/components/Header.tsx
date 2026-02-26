"use client";

import { Container, Navbar, ThemeToggle } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { useClientTemplate } from "@/components/ClientTemplateProvider";

const NAV_ITEMS = [
  { href: "/", label: "Cardapio" },
  { href: "/pedidos", label: "Meus pedidos" },
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

  return (
    <Navbar className={isQuentinhasTemplate ? "border-b-2 border-primary/40 bg-bg/90" : ""}>
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

        <nav
          className={[
            "flex items-center gap-1 p-1 text-xs font-semibold uppercase tracking-[0.08em] md:text-sm",
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
                className={[
                  isQuentinhasTemplate ? "rounded-md px-3 py-2 transition" : "rounded-full px-3 py-2 transition",
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

        <ThemeToggle storageKey="mrq-client-theme" />
      </Container>
    </Navbar>
  );
}

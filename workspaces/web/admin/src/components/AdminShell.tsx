"use client";

import { Container, Navbar, ThemeToggle } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useEffect, useMemo, useState, type ReactNode } from "react";

import { useAdminTemplate } from "@/components/AdminTemplateProvider";
import { canAccessAdminModule } from "@/lib/adminAccess";
import { fetchMe, logoutAccount } from "@/lib/api";
import { hasStoredAuthSession } from "@/lib/storage";
import type { AuthUserProfile } from "@/types/api";

type NavItem = {
  href: string;
  label: string;
};

const CLASSIC_NAV_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/modulos", label: "Módulos" },
  { href: "/modulos/relatorios", label: "Relatórios" },
  { href: "/perfil", label: "Meu perfil" },
  { href: "/sobre", label: "Sobre" },
];

const ADMINKIT_CORE_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard" },
  { href: "/modulos", label: "Módulos" },
  { href: "/modulos/fluxo-operacional", label: "Fluxo guiado" },
];

const ADMINKIT_OPERATIONS_ITEMS: NavItem[] = [
  { href: "/modulos/cardapio", label: "Receitas e cardápio" },
  { href: "/modulos/clientes", label: "Clientes" },
  { href: "/modulos/compras", label: "Compras" },
  { href: "/modulos/producao", label: "Produção" },
  { href: "/modulos/pedidos", label: "Pedidos" },
  { href: "/modulos/estoque", label: "Estoque" },
  { href: "/modulos/financeiro", label: "Financeiro" },
  { href: "/modulos/relatorios", label: "Relatórios" },
];

const ADMINKIT_PLATFORM_ITEMS: NavItem[] = [
  { href: "/modulos/auditoria-atividade", label: "Auditoria de atividade" },
  { href: "/modulos/portal", label: "Portal CMS" },
  { href: "/modulos/administracao-servidor", label: "Admin. servidor" },
  { href: "/modulos/instalacao-deploy", label: "Instalação / Deploy" },
  { href: "/modulos/monitoramento", label: "Monitoramento" },
  { href: "/modulos/usuarios-rbac", label: "Usuários e RBAC" },
  { href: "/perfil", label: "Meu perfil" },
  { href: "/sobre", label: "Sobre" },
];

const ADMINDEK_HUB_ITEMS: NavItem[] = [
  { href: "/", label: "Dashboard Prime" },
  { href: "/modulos", label: "Command Center" },
  { href: "/modulos/fluxo-operacional", label: "Wizard Operacional" },
];

const ADMINDEK_BUSINESS_ITEMS: NavItem[] = [
  { href: "/modulos/cardapio", label: "Receitas e Cardápio" },
  { href: "/modulos/clientes", label: "Clientes" },
  { href: "/modulos/compras", label: "Compras e OCR" },
  { href: "/modulos/producao", label: "Produção" },
  { href: "/modulos/pedidos", label: "Pedidos e Entrega" },
  { href: "/modulos/estoque", label: "Estoque" },
  { href: "/modulos/financeiro", label: "Financeiro" },
  { href: "/modulos/relatorios", label: "Relatórios" },
];

const ADMINDEK_PLATFORM_ITEMS: NavItem[] = [
  { href: "/modulos/monitoramento", label: "Monitoramento" },
  { href: "/modulos/auditoria-atividade", label: "Auditoria de atividade" },
  { href: "/modulos/portal", label: "Portal CMS" },
  { href: "/modulos/administracao-servidor", label: "Admin. servidor" },
  { href: "/modulos/instalacao-deploy", label: "Instalação / Deploy" },
  { href: "/modulos/usuarios-rbac", label: "Usuários e RBAC" },
  { href: "/perfil", label: "Meu perfil" },
  { href: "/sobre", label: "Sobre" },
];

function isActive(pathname: string, href: string): boolean {
  if (href === "/") {
    return pathname === "/";
  }

  return pathname === href || pathname.startsWith(`${href}/`);
}

function resolveModuleSlugFromHref(href: string): string | null {
  if (!href.startsWith("/modulos/")) {
    return null;
  }
  const parts = href.split("/").filter(Boolean);
  if (parts.length < 2) {
    return null;
  }
  return parts[1] || null;
}

function canRenderNavItem(user: AuthUserProfile, href: string): boolean {
  if (href === "/" || href === "/modulos" || href === "/perfil" || href === "/sobre") {
    return true;
  }

  const moduleSlug = resolveModuleSlugFromHref(href);
  if (!moduleSlug) {
    return true;
  }

  return canAccessAdminModule(user, moduleSlug, "read");
}

function filterNavItems(user: AuthUserProfile, items: NavItem[]): NavItem[] {
  return items.filter((item) => canRenderNavItem(user, item.href));
}

function renderSidebarLink(pathname: string, item: NavItem) {
  const active = isActive(pathname, item.href);

  return (
    <Link
      key={item.href}
      href={item.href}
      className={[
        "group inline-flex w-full items-center justify-between rounded-lg px-3 py-2 text-sm transition",
        active
          ? "bg-primary text-white shadow-sm"
          : "text-slate-200 hover:bg-slate-700 hover:text-white",
      ].join(" ")}
    >
      <span>{item.label}</span>
      <span
        aria-hidden
        className={[
          "h-2 w-2 rounded-full border border-current transition",
          active ? "bg-white/85" : "bg-transparent opacity-70 group-hover:opacity-100",
        ].join(" ")}
      />
    </Link>
  );
}

function renderClassicShell(pathname: string, children: ReactNode, user: AuthUserProfile) {
  const navItems = filterNavItems(user, CLASSIC_NAV_ITEMS);
  return (
    <>
      <Navbar>
        <Container className="flex flex-wrap items-center justify-between gap-3 py-3">
          <Link href="/" aria-label="Mr Quentinha Admin" className="shrink-0">
            <span className="inline-flex rounded-lg bg-white/95 px-2 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
              <Image
                src="/brand/original_png/logo_wordmark_original.png"
                alt="Mr Quentinha"
                width={170}
                height={65}
                priority
              />
            </span>
          </Link>

          <nav className="flex items-center gap-1 rounded-full border border-border bg-surface p-1 text-xs font-semibold uppercase tracking-[0.08em] md:text-sm">
            {navItems.map((item) => {
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

      <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-5 md:px-6 md:py-8">
        {children}
      </main>
    </>
  );
}

function renderAdminKitShell(pathname: string, children: ReactNode, user: AuthUserProfile) {
  const coreItems = filterNavItems(user, ADMINKIT_CORE_ITEMS);
  const operationItems = filterNavItems(user, ADMINKIT_OPERATIONS_ITEMS);
  const platformItems = filterNavItems(user, ADMINKIT_PLATFORM_ITEMS);
  const mobileItems = [...coreItems, ...operationItems, ...platformItems];

  return (
    <div className="flex min-h-screen bg-bg">
      <aside className="hidden w-72 shrink-0 border-r border-slate-700 bg-slate-900 text-slate-100 lg:flex lg:flex-col">
        <div className="border-b border-slate-700 px-5 py-5">
          <Link href="/" aria-label="Mr Quentinha Admin">
            <Image
              src="/brand/original_png/logo_wordmark_original.png"
              alt="Mr Quentinha"
              width={160}
              height={60}
              priority
              className="rounded-md bg-white p-1"
            />
          </Link>
          <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-300">
            Operations Kit
          </p>
        </div>

        <nav className="flex-1 space-y-6 overflow-y-auto px-3 py-4">
          <section className="space-y-2">
            <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Visão geral
            </p>
            {coreItems.map((item) => renderSidebarLink(pathname, item))}
          </section>

          <section className="space-y-2">
            <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Operação diária
            </p>
            {operationItems.map((item) => renderSidebarLink(pathname, item))}
          </section>

          <section className="space-y-2">
            <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Plataforma
            </p>
            {platformItems.map((item) => renderSidebarLink(pathname, item))}
          </section>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-border bg-surface/90 px-4 py-3 backdrop-blur md:px-6">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <div className="flex items-center gap-2 rounded-md border border-border bg-bg px-3 py-2">
              <span aria-hidden className="text-sm text-muted">
                /
              </span>
              <p className="text-sm font-medium text-text">Controle operacional em tempo real</p>
            </div>

            <div className="flex items-center gap-3">
              <span className="rounded-full border border-border bg-bg px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Template AdminKit
              </span>
              <ThemeToggle storageKey="mrq-admin-theme" />
            </div>
          </div>

          <div className="mt-3 flex gap-2 overflow-x-auto lg:hidden">
            {mobileItems.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "whitespace-nowrap rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] transition",
                    active
                      ? "border-primary bg-primary text-white"
                      : "border-border bg-bg text-muted hover:border-primary hover:text-primary",
                  ].join(" ")}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </header>

        <main className="flex-1 px-4 py-5 md:px-6 md:py-8">
          <div className="mx-auto w-full max-w-[1320px]">{children}</div>
        </main>
      </div>
    </div>
  );
}

function renderAdminDekShell(pathname: string, children: ReactNode, user: AuthUserProfile) {
  const hubItems = filterNavItems(user, ADMINDEK_HUB_ITEMS);
  const businessItems = filterNavItems(user, ADMINDEK_BUSINESS_ITEMS);
  const platformItems = filterNavItems(user, ADMINDEK_PLATFORM_ITEMS);
  const mobileItems = [...hubItems, ...businessItems, ...platformItems];

  return (
    <div className="flex min-h-screen bg-bg">
      <aside className="hidden w-[286px] shrink-0 border-r border-slate-700/70 bg-gradient-to-b from-slate-950 via-slate-900 to-slate-800 text-slate-100 lg:flex lg:flex-col">
        <div className="px-5 py-5">
          <Link href="/" aria-label="Mr Quentinha Admin">
            <Image
              src="/brand/original_png/logo_wordmark_original.png"
              alt="Mr Quentinha"
              width={170}
              height={65}
              priority
              className="rounded-md bg-white p-1.5"
            />
          </Link>
          <div className="mt-4 rounded-xl border border-slate-700/80 bg-slate-900/65 p-3">
            <p className="text-[11px] uppercase tracking-[0.16em] text-slate-400">
              Admindek Prime
            </p>
            <p className="mt-1 text-sm font-semibold text-white">
              Operação em tempo real
            </p>
            <p className="mt-1 text-xs text-slate-300">
              Ecommerce, CRM e Finance em um único painel.
            </p>
          </div>
        </div>

        <nav className="flex-1 space-y-5 overflow-y-auto px-3 pb-6">
          <section className="space-y-2">
            <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Hub
            </p>
            {hubItems.map((item) => renderSidebarLink(pathname, item))}
          </section>

          <section className="space-y-2">
            <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Business
            </p>
            {businessItems.map((item) => renderSidebarLink(pathname, item))}
          </section>

          <section className="space-y-2">
            <p className="px-2 text-[11px] font-semibold uppercase tracking-[0.18em] text-slate-400">
              Plataforma
            </p>
            {platformItems.map((item) => renderSidebarLink(pathname, item))}
          </section>
        </nav>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="border-b border-border/80 bg-white/70 px-4 py-3 backdrop-blur md:px-6 dark:bg-slate-900/55">
          <div className="flex flex-wrap items-center justify-between gap-3">
            <label className="flex min-w-[240px] flex-1 items-center gap-2 rounded-xl border border-border bg-bg px-3 py-2 text-sm text-muted shadow-sm lg:max-w-[420px]">
              <span aria-hidden className="text-base leading-none">
                ⌕
              </span>
              <input
                aria-label="Buscar no painel"
                placeholder="Buscar módulos, pedidos, receitas..."
                className="w-full bg-transparent text-sm text-text outline-none placeholder:text-muted"
              />
            </label>

            <div className="flex items-center gap-2">
              <span className="rounded-full border border-primary/35 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] text-primary">
                Template AdminDek
              </span>
              <button
                type="button"
                className="rounded-lg border border-border bg-bg px-3 py-2 text-xs font-semibold uppercase tracking-[0.08em] text-muted transition hover:border-primary hover:text-primary"
              >
                Alerts
              </button>
              <ThemeToggle storageKey="mrq-admin-theme" />
            </div>
          </div>

          <div className="mt-3 flex flex-wrap items-center gap-2">
            <span className="rounded-full border border-status-success/30 bg-status-success-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-status-success">
              pedidos online
            </span>
            <span className="rounded-full border border-status-info/30 bg-status-info-soft px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-status-info">
              sync pagamentos
            </span>
            <span className="rounded-full border border-border bg-bg px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.08em] text-muted">
              proximo fechamento 18h
            </span>
          </div>

          <div className="mt-3 flex gap-2 overflow-x-auto lg:hidden">
            {mobileItems.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={[
                    "whitespace-nowrap rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.08em] transition",
                    active
                      ? "border-primary bg-primary text-white"
                      : "border-border bg-bg text-muted hover:border-primary hover:text-primary",
                  ].join(" ")}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </header>

        <main className="flex-1 px-4 py-5 md:px-6 md:py-8">
          <div className="mx-auto w-full max-w-[1360px]">{children}</div>
        </main>
      </div>
    </div>
  );
}

export function AdminShell({ children }: { children: ReactNode }) {
  const pathname = usePathname();
  const { template } = useAdminTemplate();
  const [user, setUser] = useState<AuthUserProfile | null>(null);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    let mounted = true;

    async function bootstrap() {
      if (!hasStoredAuthSession()) {
        if (mounted) {
          setUser(null);
          setIsAuthenticated(false);
        }
        return;
      }
      try {
        const profile = await fetchMe();
        if (!mounted) {
          return;
        }
        setUser(profile);
        setIsAuthenticated(true);
      } catch {
        logoutAccount();
        if (!mounted) {
          return;
        }
        setUser(null);
        setIsAuthenticated(false);
      }
    }

    void bootstrap();
    return () => {
      mounted = false;
    };
  }, [pathname]);

  const shellUser = useMemo(() => (isAuthenticated ? user : null), [isAuthenticated, user]);

  if (!shellUser) {
    return (
      <div className="flex min-h-screen flex-col">
        <main className="mx-auto w-full max-w-6xl flex-1 px-4 py-5 md:px-6 md:py-8">{children}</main>
      </div>
    );
  }

  if (template === "admin-adminkit") {
    return renderAdminKitShell(pathname, children, shellUser);
  }

  if (template === "admin-admindek") {
    return renderAdminDekShell(pathname, children, shellUser);
  }

  return (
    <div className="flex min-h-screen flex-col">{renderClassicShell(pathname, children, shellUser)}</div>
  );
}

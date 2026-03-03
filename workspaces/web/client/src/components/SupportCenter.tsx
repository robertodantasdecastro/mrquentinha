"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

import { hasStoredAuthSession } from "@/lib/storage";
import { SupportTicketsPanel } from "./SupportTicketsPanel";

export function SupportCenter() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(false);

  useEffect(() => {
    const syncAuthState = () => {
      setIsAuthenticated(hasStoredAuthSession());
    };

    syncAuthState();
    window.addEventListener("focus", syncAuthState);
    window.addEventListener("storage", syncAuthState);

    return () => {
      window.removeEventListener("focus", syncAuthState);
      window.removeEventListener("storage", syncAuthState);
    };
  }, []);

  if (!isAuthenticated) {
    return (
      <section className="rounded-2xl border border-border bg-surface/70 p-5">
        <h2 className="text-lg font-semibold text-text">Acesso ao suporte autenticado</h2>
        <p className="mt-2 text-sm text-muted">
          Entre na sua conta para abrir e acompanhar chamados.
        </p>
        <div className="mt-4 flex flex-wrap gap-3">
          <Link
            href="/conta?next=/suporte"
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft"
          >
            Entrar para abrir chamado
          </Link>
          <Link
            href="/wiki"
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
          >
            Ver wiki de ajuda
          </Link>
        </div>
      </section>
    );
  }

  return <SupportTicketsPanel />;
}

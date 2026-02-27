"use client";

import Link from "next/link";
import { StatusPill } from "@mrquentinha/ui";

import { CustomersManagementPanel } from "@/components/modules/CustomersManagementPanel";

export const CLIENTES_BASE_PATH = "/modulos/clientes";

export const CLIENTES_MENU_ITEMS = [
  { key: "all", label: "Todos", href: CLIENTES_BASE_PATH },
  { key: "gestao", label: "Gestao", href: `${CLIENTES_BASE_PATH}/gestao#gestao` },
  { key: "compliance", label: "Compliance", href: `${CLIENTES_BASE_PATH}/compliance#compliance` },
  { key: "operacao", label: "Operacao", href: `${CLIENTES_BASE_PATH}/operacao#operacao` },
];

export type ClientesSectionKey = "all" | "gestao" | "compliance" | "operacao";

type ClientesSectionsProps = {
  activeSection?: ClientesSectionKey;
};

export function ClientesSections({ activeSection = "all" }: ClientesSectionsProps) {
  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "gestao") && (
        <section id="gestao" className="scroll-mt-24">
          <CustomersManagementPanel />
        </section>
      )}

      {(showAll || activeSection === "compliance") && (
        <section
          id="compliance"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Compliance e legislacao (Brasil)</h2>
              <p className="mt-1 text-sm text-muted">
                Governanca para LGPD, identidade do titular e trilha operacional de suporte.
              </p>
            </div>
            <StatusPill tone="info">LGPD + KYC</StatusPill>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Direitos do titular
              </p>
              <p className="mt-2 text-sm text-text">
                Acesso, correcao, eliminacao, anonimização, portabilidade e revogacao.
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Controle de prazo
              </p>
              <p className="mt-2 text-sm text-text">
                Solicitações LGPD com protocolo, status e prazo operacional para atendimento.
              </p>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-xs font-semibold uppercase tracking-[0.08em] text-muted">
                Elegibilidade de checkout
              </p>
              <p className="mt-2 text-sm text-text">
                Status da conta sincronizado com bloqueio/liberacao de pedidos no ecommerce.
              </p>
            </article>
          </div>
        </section>
      )}

      {(showAll || activeSection === "operacao") && (
        <section
          id="operacao"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Procedimentos operacionais</h2>
              <p className="mt-1 text-sm text-muted">
                Atalhos para rotinas relacionadas ao ciclo completo do cliente no ecossistema.
              </p>
            </div>
            <StatusPill tone="success">Ecommerce</StatusPill>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <Link
              href="/modulos/administracao-servidor/email#email"
              className="rounded-xl border border-border bg-bg p-4 transition hover:border-primary"
            >
              <p className="text-sm font-semibold text-text">Gestao de e-mail transacional</p>
              <p className="mt-1 text-xs text-muted">
                Revisar SMTP, remetente e envio de teste para confirmacao de conta.
              </p>
            </Link>
            <Link
              href="/modulos/pedidos"
              className="rounded-xl border border-border bg-bg p-4 transition hover:border-primary"
            >
              <p className="text-sm font-semibold text-text">Fila de pedidos e lifecycle</p>
              <p className="mt-1 text-xs text-muted">
                Verificar impacto de bloqueio de conta no checkout e no fluxo de pedido.
              </p>
            </Link>
            <Link
              href="/modulos/monitoramento"
              className="rounded-xl border border-border bg-bg p-4 transition hover:border-primary"
            >
              <p className="text-sm font-semibold text-text">Monitoramento em tempo real</p>
              <p className="mt-1 text-xs text-muted">
                Acompanhar saude da API e servicos para atendimento ao cliente sem indisponibilidade.
              </p>
            </Link>
            <Link
              href="/modulos/usuarios-rbac"
              className="rounded-xl border border-border bg-bg p-4 transition hover:border-primary"
            >
              <p className="text-sm font-semibold text-text">Perfis internos e permissao</p>
              <p className="mt-1 text-xs text-muted">
                Garantir acesso apenas para equipes de gestao e operacao autorizadas.
              </p>
            </Link>
          </div>
        </section>
      )}
    </>
  );
}

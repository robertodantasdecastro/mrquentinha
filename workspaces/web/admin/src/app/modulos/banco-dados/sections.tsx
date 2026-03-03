"use client";

import Link from "next/link";
import { StatusPill } from "@mrquentinha/ui";

import { ModuleGuide } from "@/components/modules/ModuleGuide";
import { DatabaseOpsPanel } from "@/components/modules/DatabaseOpsPanel";
import { DatabaseSshAccessPanel } from "@/components/modules/DatabaseSshAccessPanel";

export const BANCO_DADOS_BASE_PATH = "/modulos/banco-dados";

export const BANCO_DADOS_MENU_ITEMS = [
  { key: "all", label: "Todos", href: BANCO_DADOS_BASE_PATH },
  { key: "guia", label: "Guia do modulo", href: `${BANCO_DADOS_BASE_PATH}/guia#guia` },
  { key: "ssh", label: "Acesso SSH", href: `${BANCO_DADOS_BASE_PATH}/ssh#ssh` },
  { key: "backup", label: "Backups", href: `${BANCO_DADOS_BASE_PATH}/backup#backup` },
  { key: "sync-dev", label: "Sync DEV", href: `${BANCO_DADOS_BASE_PATH}/sync-dev#sync-dev` },
];

export type BancoDadosSectionKey = "all" | "guia" | "ssh" | "backup" | "sync-dev";

type BancoDadosSectionsProps = {
  activeSection?: BancoDadosSectionKey;
};

export function BancoDadosSections({ activeSection = "all" }: BancoDadosSectionsProps) {
  const showAll = activeSection === "all";

  return (
    <>
      {(showAll || activeSection === "guia") && (
        <section id="guia" className="scroll-mt-24">
          <ModuleGuide
            title="Banco de dados e continuidade operacional"
            summary="Configure SSH, gere backups remotos, restaure com seguranca e sincronize dados para DEV."
            steps={[
              {
                title: "Configurar acesso SSH",
                description: "Defina host/porta/usuario e autenticacao por chave .pem ou senha.",
              },
              {
                title: "Validar conectividade",
                description: "Execute o probe SSH antes de qualquer acao de banco.",
              },
              {
                title: "Criar backup remoto",
                description: "Gerar dump PostgreSQL customizado (.dump) com metadata.",
              },
              {
                title: "Restaurar ou sincronizar",
                description: "Restaure em producao (com confirmacao) ou replique para o DEV.",
              },
            ]}
            note="Modulo individual: visivel apenas para perfis admin com acesso tecnico."
          />
        </section>
      )}

      {(showAll || activeSection === "ssh") && (
        <section id="ssh" className="scroll-mt-24">
          <DatabaseSshAccessPanel />
        </section>
      )}

      {(showAll || activeSection === "backup") && (
        <section id="backup" className="scroll-mt-24">
          <DatabaseOpsPanel />
        </section>
      )}

      {(showAll || activeSection === "sync-dev") && (
        <section
          id="sync-dev"
          className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm"
        >
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div>
              <h2 className="text-lg font-semibold text-text">Sincronizacao de dados para DEV</h2>
              <p className="mt-1 text-sm text-muted">
                O processo utiliza backup remoto selecionado para restaurar o banco local de desenvolvimento.
              </p>
            </div>
            <StatusPill tone="info">DEV sync</StatusPill>
          </div>

          <div className="mt-4 grid gap-3 md:grid-cols-2">
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-sm font-semibold text-text">Requisitos</p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-muted">
                <li>SSH de producao validado no bloco de Acesso SSH.</li>
                <li>Utilitarios `pg_dump` e `pg_restore` disponiveis na maquina local.</li>
                <li>Ambiente em modo dev/hibrido com permissao admin.</li>
              </ul>
            </article>
            <article className="rounded-xl border border-border bg-bg p-4">
              <p className="text-sm font-semibold text-text">Governanca recomendada</p>
              <ul className="mt-2 list-disc space-y-1 pl-4 text-xs text-muted">
                <li>Executar backup remoto antes de qualquer restore critico.</li>
                <li>Registrar ticket de mudanca com data/hora e operador responsavel.</li>
                <li>Revalidar testes smoke do backend apos sincronizacao.</li>
              </ul>
            </article>
          </div>

          <div className="mt-4">
            <Link
              href="/modulos/administracao-servidor/conectividade#conectividade"
              className="inline-flex rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary"
            >
              Abrir Conectividade e dominio
            </Link>
          </div>
        </section>
      )}
    </>
  );
}

import { fetchClientConfig } from "@/lib/clientTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export const metadata = {
  title: "LGPD | Mr Quentinha",
  description: "Direitos, bases legais e operacao LGPD no Mr Quentinha.",
};

export default async function LgpdPage() {
  const config = await fetchClientConfig("lgpd");
  const heroBody = asObject(resolveSectionByKey(config.sections, "hero")?.body_json);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          {asString(heroBody.kicker, "LGPD em pratica")}
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">
          {asString(heroBody.headline, "LGPD e seus direitos")}
        </h1>
        <p className="mt-3 max-w-3xl text-sm text-muted">
          {asString(
            heroBody.subheadline,
            "Entenda como o Mr Quentinha atende as obrigacoes da Lei Geral de Protecao de Dados (Lei nº 13.709/2018) em todo o ecossistema.",
          )}
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Direitos do titular</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>Confirmacao de tratamento e acesso aos dados.</li>
            <li>Correcao de dados incompletos ou desatualizados.</li>
            <li>Portabilidade, anonimização e eliminacao quando aplicavel.</li>
            <li>Informacao sobre compartilhamentos e revogacao de consentimento.</li>
          </ul>
        </article>

        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Como solicitar</h2>
          <p className="mt-3 text-sm text-muted">
            Solicitacoes podem ser abertas no Web Admin (para clientes corporativos)
            ou via email em contato@mrquentinha.com.br. Informaremos um protocolo de atendimento.
          </p>
          <p className="mt-3 text-sm text-muted">
            As solicitacoes sao atendidas de forma gratuita, com resposta imediata
            para confirmacao/acesso; pedidos com origem/criterios/finalidade sao respondidos
            em ate 15 dias, conforme orientacao da ANPD.
          </p>
        </article>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-bg p-5">
          <h2 className="text-lg font-semibold text-text">Retencao e seguranca</h2>
          <p className="mt-3 text-sm text-muted">
            Mantemos dados pelo tempo necessario para obrigacoes legais e operacionais.
            Dados sensiveis recebem criptografia e controles de acesso no Web Admin.
          </p>
        </article>

        <article className="rounded-2xl border border-border bg-bg p-5">
          <h2 className="text-lg font-semibold text-text">Bases legais</h2>
          <p className="mt-3 text-sm text-muted">
            Operamos com base legal adequada: execucao de contrato, cumprimento legal,
            legitimo interesse e consentimento quando necessario.
          </p>
        </article>
      </section>
    </div>
  );
}

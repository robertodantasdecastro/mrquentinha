import { fetchClientConfig } from "@/lib/clientTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export const metadata = {
  title: "Politica de Privacidade | Mr Quentinha",
  description: "Politica de privacidade do Mr Quentinha.",
};

export default async function PrivacidadePage() {
  const config = await fetchClientConfig("privacidade");
  const heroBody = asObject(resolveSectionByKey(config.sections, "hero")?.body_json);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          {asString(heroBody.kicker, "Privacidade e seguranca")}
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">
          {asString(heroBody.headline, "Politica de Privacidade")}
        </h1>
        <p className="mt-3 max-w-3xl text-sm text-muted">
          {asString(
            heroBody.subheadline,
            "Transparencia sobre coleta, uso e protecao de dados pessoais no ecossistema Mr Quentinha, alinhada a Lei Geral de Protecao de Dados (Lei nº 13.709/2018).",
          )}
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Dados que coletamos</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>Identificacao e contato (nome, email, telefone, endereco).</li>
            <li>Preferencias de compra e historico de pedidos.</li>
            <li>Dados operacionais (logs de acesso, dispositivo e navegacao).</li>
            <li>Consentimentos LGPD e escolhas de comunicacao.</li>
          </ul>
        </article>

        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Como usamos</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>Processar pedidos, pagamentos e entregas.</li>
            <li>Atendimento ao cliente, suporte e comunicacoes.</li>
            <li>Seguranca, prevencao a fraude e auditoria.</li>
            <li>Melhoria continua de produtos e experiencia.</li>
          </ul>
        </article>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-bg p-5">
          <h2 className="text-lg font-semibold text-text">Base legal</h2>
          <p className="mt-3 text-sm text-muted">
            Tratamos dados com base na execucao de contrato, cumprimento legal,
            legitimo interesse e consentimento quando aplicavel.
          </p>
        </article>

        <article className="rounded-2xl border border-border bg-bg p-5">
          <h2 className="text-lg font-semibold text-text">Seus direitos</h2>
          <p className="mt-3 text-sm text-muted">
            Voce pode solicitar confirmacao de tratamento, acesso, correcao,
            portabilidade, eliminacao, informacoes sobre compartilhamento e
            revogacao de consentimento, conforme a LGPD.
          </p>
        </article>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Prazo de resposta</h2>
          <p className="mt-3 text-sm text-muted">
            A confirmacao de tratamento e o acesso sao providenciados de imediato.
            Quando a solicitacao envolve origem dos dados, criterios utilizados ou finalidade,
            a resposta ocorre em ate 15 dias, conforme orientacao da ANPD.
            Para outros direitos, aplicamos o prazo definido em regulamento especifico.
          </p>
        </article>

        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Seguranca e criptografia</h2>
          <p className="mt-3 text-sm text-muted">
            Dados sensiveis sao protegidos com criptografia em repouso e controles
            de acesso no Web Admin, com registros de auditoria.
          </p>
        </article>
      </section>

      <section className="rounded-2xl border border-border bg-surface/70 p-5">
        <h2 className="text-lg font-semibold text-text">Contato LGPD</h2>
        <p className="mt-3 text-sm text-muted">
          Para solicitacoes LGPD, utilize o canal oficial no Web Admin ou envie email para
          contato@mrquentinha.com.br com o assunto &quot;LGPD&quot;.
        </p>
      </section>
    </div>
  );
}

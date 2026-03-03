import { fetchPortalConfig } from "@/lib/portalTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export const metadata = {
  title: "Termos de Uso | Mr Quentinha",
  description: "Termos de uso do ecossistema Mr Quentinha.",
};

export default async function TermosPage() {
  const portalConfig = await fetchPortalConfig("termos");
  const heroBody = asObject(resolveSectionByKey(portalConfig.sections, "hero")?.body_json);

  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          {asString(heroBody.kicker, "Termos e condicoes")}
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">
          {asString(heroBody.headline, "Termos de Uso")}
        </h1>
        <p className="mt-3 max-w-3xl text-sm text-muted">
          {asString(
            heroBody.subheadline,
            "Condicoes para uso do portal, web client, app e servicos do Mr Quentinha.",
          )}
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Conta e acesso</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>Informacoes devem ser verdadeiras e atualizadas.</li>
            <li>O uso da conta e pessoal e intransferivel.</li>
            <li>Voce e responsavel pela seguranca das credenciais.</li>
          </ul>
        </article>

        <article className="rounded-2xl border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Pedidos e entregas</h2>
          <ul className="mt-3 space-y-2 text-sm text-muted">
            <li>Os pedidos seguem horarios e disponibilidade de cardapio.</li>
            <li>Informacoes de entrega precisam estar corretas.</li>
            <li>Politicas de cancelamento variam por tipo de pedido.</li>
          </ul>
        </article>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-2xl border border-border bg-bg p-5">
          <h2 className="text-lg font-semibold text-text">Condutas vedadas</h2>
          <p className="mt-3 text-sm text-muted">
            E proibido usar o sistema para fraudes, abuso, engenharia reversa ou
            comprometimento da seguranca e privacidade de terceiros.
          </p>
        </article>

        <article className="rounded-2xl border border-border bg-bg p-5">
          <h2 className="text-lg font-semibold text-text">Atualizacoes</h2>
          <p className="mt-3 text-sm text-muted">
            Os termos podem ser atualizados conforme evolucao do servico. Avisaremos
            em canais oficiais quando houver mudancas relevantes.
          </p>
        </article>
      </section>
    </div>
  );
}

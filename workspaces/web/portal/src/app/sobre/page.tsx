import { PortalPageIntro } from "@/components/PortalPageIntro";
import { fetchPortalConfig } from "@/lib/portalTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export const metadata = {
  title: "Sobre o Mr Quentinha",
};

export default async function SobrePage() {
  const portalConfig = await fetchPortalConfig("sobre");
  const heroBody = asObject(resolveSectionByKey(portalConfig.sections, "hero")?.body_json);

  return (
    <div className="space-y-6">
      <PortalPageIntro
        kicker={asString(heroBody.kicker, "Quem somos")}
        title={asString(heroBody.headline, "Muito prazer, somos o Mr Quentinha")}
        description={asString(
          heroBody.subheadline,
          "A alimentacao saudavel nao precisa dar trabalho. Unimos processo de cozinha, previsibilidade de entrega e tecnologia para operar vendas e atendimento com padrao.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Como funciona", href: "/como-funciona", tone: "ghost" },
          { label: "Vendas no app", href: "/app", tone: "primary" },
          { label: "Contato", href: "/contato", tone: "soft" },
        ]}
      />

      <section className="rounded-2xl border border-border bg-surface/70 p-6 md:p-8">
        <h2 className="text-2xl font-bold text-text">Nossa historia</h2>
        <div className="mt-4 space-y-4 text-sm leading-6 text-muted md:text-base">
          <p>
            O projeto nasceu para resolver uma dor real: manter uma rotina nutritiva
            mesmo com agenda apertada. O ecossistema combina cardapio organizado,
            producao padronizada e atendimento integrado.
          </p>
          <p>
            Hoje, o mesmo fluxo cobre portal institucional, web cliente e operacao
            administrativa. Resultado: menos friccao na compra e mais previsibilidade
            para cozinha, estoque e financeiro.
          </p>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-xl border border-border bg-bg p-5">
          <h3 className="text-lg font-semibold text-primary">Qualidade</h3>
          <p className="mt-2 text-sm text-muted">
            Ingredientes selecionados e preparo com padrao operacional.
          </p>
        </article>
        <article className="rounded-xl border border-border bg-bg p-5">
          <h3 className="text-lg font-semibold text-primary">Tecnologia</h3>
          <p className="mt-2 text-sm text-muted">
            Template por canal, dados centralizados e evolucao continua por modulo.
          </p>
        </article>
        <article className="rounded-xl border border-border bg-bg p-5">
          <h3 className="text-lg font-semibold text-primary">Escala</h3>
          <p className="mt-2 text-sm text-muted">
            Arquitetura preparada para vendas web/mobile e governanca operacional.
          </p>
        </article>
      </section>
    </div>
  );
}

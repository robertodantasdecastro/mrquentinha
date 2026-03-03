import { CardapioList } from "@/components/CardapioList";
import { fetchPortalConfig } from "@/lib/portalTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export const metadata = {
  title: "Cardapio",
  description: "Consulta do cardapio por data em tempo real.",
};

export default async function CardapioPage() {
  const portalConfig = await fetchPortalConfig("cardapio");
  const heroBody = asObject(resolveSectionByKey(portalConfig.sections, "hero")?.body_json);

  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
          {asString(heroBody.kicker, "API ao vivo")}
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">
          {asString(heroBody.headline, "Cardapio do dia")}
        </h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
          {asString(
            heroBody.subheadline,
            "Selecione a data para consultar itens e precos atualizados direto do backend.",
          )}
        </p>
      </section>

      <CardapioList />
    </div>
  );
}

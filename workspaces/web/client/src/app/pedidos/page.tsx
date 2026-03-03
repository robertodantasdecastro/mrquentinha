import { OrderHistoryList } from "@/components/OrderHistoryList";
import { fetchClientConfig } from "@/lib/clientTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export default async function PedidosPage() {
  const config = await fetchClientConfig("pedidos");
  const heroBody = asObject(resolveSectionByKey(config.sections, "hero")?.body_json);

  return (
    <section className="space-y-4">
      <header className="rounded-2xl border border-border bg-surface/70 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          {asString(heroBody.kicker, "Meus pedidos")}
        </p>
        <h1 className="mt-1 text-2xl font-bold text-text">
          {asString(heroBody.headline, "Acompanhe seu historico")}
        </h1>
        <p className="mt-2 text-sm text-muted">
          {asString(
            heroBody.subheadline,
            "Do login ao recebimento: acompanhe status de preparo, entrega e confirme o recebimento aqui.",
          )}
        </p>
      </header>

      <OrderHistoryList />
    </section>
  );
}

import { PortalPageIntro } from "@/components/PortalPageIntro";
import { HowToHeat } from "@/components/letsfit";
import { fetchPortalConfig } from "@/lib/portalTemplate";
import { asArray, asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

export const metadata = {
  title: "Como funciona",
};

const DEFAULT_STEPS = [
  {
    step: 1,
    title: "Voce escolhe",
    description:
      "Acesse o cardapio por data ou use kits recomendados para acelerar a compra.",
  },
  {
    step: 2,
    title: "Nos preparamos",
    description:
      "A cozinha segue padrao operacional para garantir qualidade e previsibilidade.",
  },
  {
    step: 3,
    title: "Voce acompanha",
    description:
      "Pedido, pagamento e suporte ficam centralizados no app do cliente.",
  },
];

function resolveSteps(value: unknown): Array<{ title: string; description: string }> {
  const items = asArray(value);
  const steps = items
    .map((item) => {
      const body = asObject(item);
      const title = asString(body.title);
      const description = asString(body.description);
      if (!title || !description) {
        return null;
      }
      return { title, description };
    })
    .filter((item): item is { title: string; description: string } => item !== null);

  if (steps.length > 0) {
    return steps;
  }
  return DEFAULT_STEPS.map((item) => ({
    title: item.title,
    description: item.description,
  }));
}

export default async function ComoFuncionaPage() {
  const portalConfig = await fetchPortalConfig("como-funciona");
  const heroBody = asObject(resolveSectionByKey(portalConfig.sections, "hero")?.body_json);
  const stepsBody = asObject(resolveSectionByKey(portalConfig.sections, "steps")?.body_json);
  const steps = resolveSteps(stepsBody.items);

  return (
    <div className="space-y-8">
      <PortalPageIntro
        kicker={asString(heroBody.kicker, "Jornada completa")}
        title={asString(heroBody.headline, "Como funciona o ecossistema Mr Quentinha")}
        description={asString(
          heroBody.subheadline,
          "Do portal institucional ate a finalizacao do pedido no app, toda a jornada foi organizada para reduzir atrito na venda e no atendimento.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Abrir vendas no app", href: "/app", tone: "primary" },
          { label: "Suporte", href: "/suporte", tone: "ghost" },
          { label: "Wiki", href: "/wiki", tone: "soft" },
        ]}
      />

      <section className="grid gap-4 md:grid-cols-3">
        {steps.map((item, index) => (
          <article
            key={`${index}:${item.title}`}
            className="rounded-2xl border border-border bg-surface/70 p-6"
          >
            <div className="inline-flex h-10 w-10 items-center justify-center rounded-full bg-primary text-sm font-bold text-white">
              {index + 1}
            </div>
            <h3 className="mt-4 text-xl font-bold text-text">{item.title}</h3>
            <p className="mt-2 text-sm leading-6 text-muted">{item.description}</p>
          </article>
        ))}
      </section>

      <HowToHeat />
    </div>
  );
}

import { headers } from "next/headers";

import { PortalPageIntro } from "@/components/PortalPageIntro";
import { asArray, asObject, asString, resolveSectionByKey } from "@/lib/portalContent";
import { extractHostname, resolveFrontendUrl } from "@/lib/networkHost";
import { fetchPortalConfig } from "@/lib/portalTemplate";

const CLIENT_AREA_URL =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

export const metadata = {
  title: "Contato",
  description: "Canal institucional de contato do Mr Quentinha.",
};

export default async function ContatoPage() {
  const portalConfig = await fetchPortalConfig("contato");
  const heroBody = asObject(resolveSectionByKey(portalConfig.sections, "hero")?.body_json);
  const channelsBody = asObject(resolveSectionByKey(portalConfig.sections, "channels")?.body_json);
  const channels = asArray(channelsBody.items)
    .map((item) => {
      const body = asObject(item);
      const title = asString(body.title);
      const description = asString(body.description);
      const value = asString(body.value);
      if (!title || !description || !value) {
        return null;
      }
      return { title, description, value };
    })
    .filter(
      (item): item is { title: string; description: string; value: string } =>
        item !== null,
    );

  const requestHeaders = await headers();
  const requestHostname = extractHostname(
    requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "",
  );
  const clientAreaUrl = resolveFrontendUrl(requestHostname, 3001, CLIENT_AREA_URL);

  return (
    <div className="space-y-6">
      <PortalPageIntro
        kicker={asString(heroBody.kicker, "Fale com o Mr Quentinha")}
        title={asString(heroBody.headline, "Contato institucional e comercial")}
        description={asString(
          heroBody.subheadline,
          "Use esta central para parcerias, implantacao do ecossistema e orientacao comercial. Para atendimento de pedidos, use o suporte no app do cliente.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Area de vendas (app)", href: clientAreaUrl, external: true, tone: "primary" },
          { label: "Central de suporte", href: "/suporte", tone: "ghost" },
          { label: "Wiki operacional", href: "/wiki", tone: "soft" },
        ]}
      />

      <section className="grid gap-4 md:grid-cols-3">
        {(channels.length > 0
          ? channels
          : [
              {
                title: "Comercial e parcerias",
                description: "Implantacao e evolucao de operacao.",
                value: "contato@mrquentinha.com.br",
              },
              {
                title: "Suporte operacional",
                description: "Demandas de producao, pedidos e atendimento.",
                value: "suporte@mrquentinha.com.br",
              },
              {
                title: "Horario",
                description: "Segunda a sexta, das 08h as 18h",
                value: "Sao Paulo - SP",
              },
            ]).map((channel) => (
          <article key={channel.title} className="rounded-lg border border-border bg-surface/70 p-5">
            <h2 className="text-lg font-semibold text-text">{channel.title}</h2>
            <p className="mt-3 text-sm text-muted">{channel.description}</p>
            <p className="mt-2 text-sm text-muted">{channel.value}</p>
          </article>
        ))}
      </section>
    </div>
  );
}

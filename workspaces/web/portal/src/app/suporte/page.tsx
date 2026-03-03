import { headers } from "next/headers";

import { PortalPageIntro } from "@/components/PortalPageIntro";
import { extractHostname, resolveFrontendUrl } from "@/lib/networkHost";
import { fetchPortalConfig, resolveSectionByKey } from "@/lib/portalTemplate";

const CLIENT_AREA_URL =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

type SupportChannel = {
  title: string;
  description: string;
  value: string;
};

function asObject(value: unknown): Record<string, unknown> {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as Record<string, unknown>;
  }
  return {};
}

function asString(value: unknown, fallback: string = ""): string {
  if (typeof value === "string" && value.trim()) {
    return value.trim();
  }
  return fallback;
}

function asArray(value: unknown): unknown[] {
  return Array.isArray(value) ? value : [];
}

function resolveSupportChannels(value: unknown): SupportChannel[] {
  const items = asArray(value);
  const resolved = items
    .map((item) => {
      const body = asObject(item);
      const title = asString(body.title);
      const description = asString(body.description);
      const valueField = asString(body.value);

      if (!title || !description || !valueField) {
        return null;
      }

      return {
        title,
        description,
        value: valueField,
      };
    })
    .filter((item): item is SupportChannel => item !== null);

  if (resolved.length > 0) {
    return resolved;
  }

  return [
    {
      title: "Suporte cliente",
      description: "Fluxo recomendado: app do cliente - menu Suporte - abertura de chamado.",
      value: "app.mrquentinha.com.br/suporte",
    },
    {
      title: "Suporte operacional",
      description: "Atendimento comercial e operacional.",
      value: "suporte@mrquentinha.com.br",
    },
  ];
}

export const metadata = {
  title: "Suporte",
  description: "Central de suporte do ecossistema Mr Quentinha.",
};

export default async function SuportePage() {
  const portalConfig = await fetchPortalConfig("suporte");
  const sections = portalConfig.sections ?? [];
  const heroBody = asObject(resolveSectionByKey(sections, "hero")?.body_json);
  const channelsBody = asObject(resolveSectionByKey(sections, "channels")?.body_json);
  const supportChannels = resolveSupportChannels(channelsBody.items);

  const requestHeaders = await headers();
  const requestHostname = extractHostname(
    requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "",
  );
  const clientAreaUrl = resolveFrontendUrl(requestHostname, 3001, CLIENT_AREA_URL);

  return (
    <div className="space-y-6">
      <PortalPageIntro
        kicker={asString(heroBody.kicker, "Central de suporte")}
        title={asString(heroBody.headline, "Suporte para vendas, pedidos e operacao")}
        description={asString(
          heroBody.subheadline,
          "Clientes finais devem abrir chamados autenticados no app. Equipes comerciais e operacionais podem usar os canais institucionais abaixo.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Abrir chamado no app", href: `${clientAreaUrl}/suporte`, external: true, tone: "primary" },
          { label: "Wiki operacional", href: "/wiki", tone: "ghost" },
          { label: "Contato institucional", href: "/contato", tone: "soft" },
        ]}
      />

      <section className="grid gap-4 md:grid-cols-2">
        {supportChannels.map((channel) => (
          <article key={channel.title} className="rounded-lg border border-border bg-surface/70 p-5">
            <h2 className="text-lg font-semibold text-text">{channel.title}</h2>
            <p className="mt-2 text-sm text-muted">{channel.description}</p>
            <p className="mt-3 text-sm font-medium text-text">{channel.value}</p>
          </article>
        ))}
      </section>
    </div>
  );
}

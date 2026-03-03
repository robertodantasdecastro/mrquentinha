import Link from "next/link";
import { headers } from "next/headers";

import { PortalPageIntro } from "@/components/PortalPageIntro";
import { extractHostname, resolveFrontendUrl } from "@/lib/networkHost";
import { fetchPortalConfig, resolveSectionByKey } from "@/lib/portalTemplate";

const CLIENT_AREA_URL =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

const WIKI_BLOCKS = [
  {
    title: "Operacao comercial",
    description: "Fluxo recomendado para venda no app e acompanhamento de pedido.",
    links: [
      { label: "Cardapio publico", href: "/cardapio" },
      { label: "Jornada no app", href: "/app" },
      { label: "Central de suporte", href: "/suporte" },
    ],
  },
  {
    title: "Governanca e conformidade",
    description: "Politicas de privacidade, termos e diretrizes LGPD.",
    links: [
      { label: "Privacidade", href: "/privacidade" },
      { label: "Termos de uso", href: "/termos" },
      { label: "LGPD", href: "/lgpd" },
    ],
  },
  {
    title: "Institucional",
    description: "Contexto de marca, operacao e canal de contato.",
    links: [
      { label: "Sobre", href: "/sobre" },
      { label: "Como funciona", href: "/como-funciona" },
      { label: "Contato", href: "/contato" },
    ],
  },
];

type WikiTopic = {
  title: string;
  href: string;
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

function resolveWikiTopics(value: unknown): WikiTopic[] {
  const items = asArray(value);
  const resolved = items
    .map((item) => {
      const body = asObject(item);
      const title = asString(body.title);
      const href = asString(body.href);
      if (!title || !href) {
        return null;
      }
      return {
        title,
        href,
      };
    })
    .filter((item): item is WikiTopic => item !== null);

  if (resolved.length > 0) {
    return resolved;
  }

  return [
    { title: "Operacao comercial", href: "/app" },
    { title: "Suporte e chamados", href: "/suporte" },
    { title: "Compliance e LGPD", href: "/lgpd" },
  ];
}

export const metadata = {
  title: "Wiki",
  description: "Base de conhecimento operacional do ecossistema Mr Quentinha.",
};

export default async function WikiPage() {
  const portalConfig = await fetchPortalConfig("wiki");
  const sections = portalConfig.sections ?? [];
  const heroBody = asObject(resolveSectionByKey(sections, "hero")?.body_json);
  const topicsBody = asObject(resolveSectionByKey(sections, "topics")?.body_json);
  const wikiTopics = resolveWikiTopics(topicsBody.items);

  const requestHeaders = await headers();
  const requestHostname = extractHostname(
    requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "",
  );
  const clientAreaUrl = resolveFrontendUrl(requestHostname, 3001, CLIENT_AREA_URL);

  return (
    <div className="space-y-6">
      <PortalPageIntro
        kicker={asString(heroBody.kicker, "Wiki operacional")}
        title={asString(heroBody.headline, "Base de conhecimento do ecossistema")}
        description={asString(
          heroBody.subheadline,
          "Documentacao orientada a operacao diaria: vendas no app, suporte, conformidade e fluxo institucional.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Abrir vendas no app", href: clientAreaUrl, external: true, tone: "primary" },
          { label: "Suporte", href: "/suporte", tone: "ghost" },
          { label: "Contato", href: "/contato", tone: "soft" },
        ]}
      />

      <section className="rounded-lg border border-border bg-surface/70 p-5">
        <h2 className="text-lg font-semibold text-text">Atalhos do template ativo</h2>
        <div className="mt-3 flex flex-wrap gap-2">
          {wikiTopics.map((topic) => (
            <Link
              key={`topic:${topic.href}:${topic.title}`}
              className="rounded-md border border-border bg-bg px-3 py-2 text-sm font-medium text-text transition hover:border-primary hover:text-primary"
              href={topic.href}
            >
              {topic.title}
            </Link>
          ))}
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-3">
        {WIKI_BLOCKS.map((block) => (
          <article key={block.title} className="rounded-lg border border-border bg-surface/70 p-5">
            <h2 className="text-lg font-semibold text-text">{block.title}</h2>
            <p className="mt-2 text-sm text-muted">{block.description}</p>
            <div className="mt-4 space-y-2">
              {block.links.map((link) => (
                <Link
                  key={`${block.title}:${link.href}`}
                  className="block rounded-md border border-border bg-bg px-3 py-2 text-sm font-medium text-text transition hover:border-primary hover:text-primary"
                  href={link.href}
                >
                  {link.label}
                </Link>
              ))}
            </div>
          </article>
        ))}
      </section>
    </div>
  );
}

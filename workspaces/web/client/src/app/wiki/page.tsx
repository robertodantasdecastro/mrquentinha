import Link from "next/link";

import { ClientPageIntro } from "@/components/ClientPageIntro";
import { fetchClientConfig } from "@/lib/clientTemplate";
import { asArray, asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

const DEFAULT_WIKI_GROUPS = [
  {
    title: "Conta e acesso",
    description: "Cadastro, login, validacao de e-mail e atualizacao de dados.",
    links: [
      { label: "Minha conta", href: "/conta" },
      { label: "Politica de privacidade", href: "/privacidade" },
      { label: "Termos de uso", href: "/termos" },
    ],
  },
  {
    title: "Pedidos e pagamento",
    description: "Fluxo de compra, meios de pagamento e acompanhamento do pedido.",
    links: [
      { label: "Cardapio", href: "/cardapio" },
      { label: "Meus pedidos", href: "/pedidos" },
      { label: "Abrir suporte", href: "/suporte" },
    ],
  },
  {
    title: "Compliance e dados",
    description: "Direitos LGPD e canal de atendimento para solicitacoes.",
    links: [
      { label: "LGPD", href: "/lgpd" },
      { label: "Privacidade", href: "/privacidade" },
      { label: "Suporte", href: "/suporte" },
    ],
  },
];

type WikiGroup = {
  title: string;
  description: string;
  links: Array<{ label: string; href: string }>;
};

function resolveWikiGroups(value: unknown): WikiGroup[] {
  const items = asArray(value);
  const groups = items
    .map((item) => {
      const body = asObject(item);
      const title = asString(body.title);
      const description = asString(body.description);
      const links = asArray(body.links)
        .map((link) => {
          const linkBody = asObject(link);
          const label = asString(linkBody.label);
          const href = asString(linkBody.href);
          if (!label || !href) {
            return null;
          }
          return { label, href };
        })
        .filter((link): link is { label: string; href: string } => link !== null);

      if (!title || !description || links.length === 0) {
        return null;
      }

      return { title, description, links };
    })
    .filter((group): group is WikiGroup => group !== null);

  if (groups.length > 0) {
    return groups;
  }
  return DEFAULT_WIKI_GROUPS;
}

export const metadata = {
  title: "Wiki",
  description: "Base de ajuda do Web Cliente Mr Quentinha.",
};

export default async function WikiPage() {
  const config = await fetchClientConfig("wiki");
  const heroBody = asObject(resolveSectionByKey(config.sections, "hero")?.body_json);
  const groupsBody = asObject(resolveSectionByKey(config.sections, "groups")?.body_json);
  const groups = resolveWikiGroups(groupsBody.items);

  return (
    <div className="space-y-4">
      <ClientPageIntro
        kicker={asString(heroBody.kicker, "Wiki")}
        title={asString(heroBody.headline, "Base de ajuda do cliente")}
        description={asString(
          heroBody.subheadline,
          "Guias rapidos para compras, pedidos, conta e suporte no app web.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Abrir suporte", href: "/suporte", tone: "primary" },
          { label: "Ir para cardapio", href: "/cardapio", tone: "ghost" },
          { label: "Minha conta", href: "/conta", tone: "soft" },
        ]}
      />

      <section className="grid gap-4 md:grid-cols-3">
        {groups.map((group) => (
          <article key={group.title} className="rounded-2xl border border-border bg-bg p-4">
            <h2 className="text-base font-semibold text-text">{group.title}</h2>
            <p className="mt-2 text-sm text-muted">{group.description}</p>
            <div className="mt-4 space-y-2">
              {group.links.map((link) => (
                <Link
                  key={`${group.title}:${link.href}`}
                  href={link.href}
                  className="block rounded-md border border-border bg-surface px-3 py-2 text-sm font-medium text-text transition hover:border-primary hover:text-primary"
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

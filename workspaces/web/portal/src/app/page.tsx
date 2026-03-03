import Link from "next/link";
import { headers } from "next/headers";

import { CardapioList } from "@/components/CardapioList";
import { Hero } from "@/components/Hero";
import {
  BenefitsBar,
  Categories,
  Faq,
  HeroLetsFit,
  HowToHeat,
  KitSimulator,
} from "@/components/letsfit";
import {
  fetchPortalConfig,
  resolveSectionByKey,
  type PortalConfigPayload,
} from "@/lib/portalTemplate";
import { extractHostname, resolveFrontendUrl } from "@/lib/networkHost";

const ADMIN_URL =
  process.env.NEXT_PUBLIC_ADMIN_URL?.trim() || "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

type JsonObject = Record<string, unknown>;

function asObject(value: unknown): JsonObject {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    return value as JsonObject;
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

function parseCta(
  value: unknown,
  fallbackLabel: string,
  fallbackHref: string,
): { label: string; href: string } {
  const body = asObject(value);
  return {
    label: asString(body.label, fallbackLabel),
    href: asString(body.href, fallbackHref),
  };
}

function resolveLetsFitContent(portalConfig: PortalConfigPayload) {
  const sections = portalConfig.sections ?? [];
  const heroSection = resolveSectionByKey(sections, "hero");
  const benefitsSection = resolveSectionByKey(sections, "benefits");
  const categoriesSection = resolveSectionByKey(sections, "categories");
  const kitSection = resolveSectionByKey(sections, "kit");
  const howToHeatSection = resolveSectionByKey(sections, "how_to_heat");
  const faqSection = resolveSectionByKey(sections, "faq");

  const heroBody = asObject(heroSection?.body_json);
  const benefitsBody = asObject(benefitsSection?.body_json);
  const categoriesBody = asObject(categoriesSection?.body_json);
  const kitBody = asObject(kitSection?.body_json);
  const howToHeatBody = asObject(howToHeatSection?.body_json);
  const faqBody = asObject(faqSection?.body_json);

  const ctaPrimary = parseCta(heroBody.cta_primary, "Ver cardapio", "/cardapio");
  const ctaSecondary = parseCta(
    heroBody.cta_secondary,
    "Como funciona",
    "/como-funciona",
  );

  const rawBenefits = asArray(benefitsBody.items);
  const benefitItems = rawBenefits
    .map((item) => {
      if (typeof item === "string") {
        return {
          text: item,
        };
      }
      const body = asObject(item);
      const text = asString(body.text);
      if (!text) {
        return null;
      }
      return {
        text,
        icon: asString(body.icon),
      };
    })
    .filter((item): item is { text: string; icon?: string } => item !== null);

  const rawCategories = asArray(categoriesBody.items);
  const mappedCategories = rawCategories.map<
    { title: string; description: string; image_url?: string } | null
  >((item) => {
      const body = asObject(item);
      const title = asString(body.title || body.name);
      const description = asString(body.description);
      if (!title || !description) {
        return null;
      }
      const imageUrl = asString(body.image_url);
      if (!imageUrl) {
        return {
          title,
          description,
        };
      }
      return {
        title,
        description,
        image_url: imageUrl,
      };
    });
  const categoryItems = mappedCategories
    .filter(
      (item): item is { title: string; description: string; image_url?: string } =>
        item !== null,
    );

  const rawHeatCards = asArray(howToHeatBody.cards);
  const heatCards = rawHeatCards
    .map((item) => {
      const body = asObject(item);
      const title = asString(body.title);
      const description = asString(body.description);
      if (!title || !description) {
        return null;
      }
      return {
        tone: asString(body.tone) === "cold" ? "cold" : "hot",
        title,
        description,
      };
    })
    .filter(
      (item): item is { tone: "cold" | "hot"; title: string; description: string } =>
        item !== null,
    );

  const rawFaq = asArray(faqBody.items);
  const faqItems = rawFaq
    .map((item) => {
      const body = asObject(item);
      const question = asString(body.question);
      const answer = asString(body.answer);
      if (!question || !answer) {
        return null;
      }
      return {
        question,
        answer,
      };
    })
    .filter((item): item is { question: string; answer: string } => item !== null);

  return {
    hero: {
      kicker: asString(heroBody.kicker) || undefined,
      headline: asString(heroBody.headline) || undefined,
      subheadline: asString(heroBody.subheadline) || undefined,
      ctaPrimaryLabel: ctaPrimary.label,
      ctaPrimaryHref: ctaPrimary.href,
      ctaSecondaryLabel: ctaSecondary.label,
      ctaSecondaryHref: ctaSecondary.href,
      backgroundImageUrl: asString(heroBody.background_image_url) || undefined,
    },
    benefits: benefitItems.length > 0 ? benefitItems : undefined,
    categories: {
      title: asString(categoriesBody.title, "Escolha seu objetivo"),
      subtitle: asString(
        categoriesBody.subtitle,
        "Temos uma linha de produtos pensada para cada necessidade do seu corpo",
      ),
      items: categoryItems.length > 0 ? categoryItems : undefined,
    },
    kit: {
      kicker: asString(kitBody.kicker) || undefined,
      headline: asString(kitBody.headline) || undefined,
      description: asString(kitBody.description) || undefined,
      ctaLabel: asString(kitBody.cta_label) || undefined,
      ctaHref: asString(kitBody.cta_href, "/cardapio"),
    },
    heat: {
      title: asString(howToHeatBody.title) || undefined,
      subtitle: asString(howToHeatBody.subheadline) || undefined,
      cards: heatCards.length > 0 ? heatCards : undefined,
    },
    faq: {
      title: asString(faqBody.title, "Duvidas frequentes"),
      items: faqItems.length > 0 ? faqItems : undefined,
    },
    cardapio: {
      title: asString(heroBody.cardapio_title, "Cardapio de hoje"),
      subtitle: asString(
        heroBody.cardapio_subtitle,
        "Peca ate 11h para entrega no mesmo dia",
      ),
    },
  };
}

function HomeClassic({
  adminUrl,
  clientAreaUrl,
}: {
  adminUrl: string;
  clientAreaUrl: string;
}) {
  return (
    <div className="space-y-8 md:space-y-10">
      <Hero />

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-lg border border-border bg-bg p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Operacao
          </p>
          <h2 className="mt-2 text-xl font-semibold text-text">Cardapio e producao</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            Planeje o cardapio por data e sincronize cozinha, estoque e compras.
          </p>
        </article>

        <article className="rounded-lg border border-border bg-bg p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Comercial
          </p>
          <h2 className="mt-2 text-xl font-semibold text-text">Pedidos e clientes</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            Experiencia simples para o cliente com consulta de cardapio e pedido.
          </p>
        </article>

        <article className="rounded-lg border border-border bg-bg p-5">
          <p className="text-xs font-semibold uppercase tracking-[0.14em] text-primary">
            Financeiro
          </p>
          <h2 className="mt-2 text-xl font-semibold text-text">AP, AR e caixa</h2>
          <p className="mt-3 text-sm leading-6 text-muted">
            Controle de contas e visao gerencial para decisao rapida no dia a dia.
          </p>
        </article>
      </section>

      <section className="rounded-lg border border-border bg-surface/80 p-6 md:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
          Acesso rapido
        </p>
        <h2 className="mt-2 text-2xl font-bold text-text">Ecossistema conectado</h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
          O portal institucional tambem funciona como ponte de entrada para o app,
          modulo de gestao e area do cliente.
        </p>

        <div className="mt-6 flex flex-wrap gap-3">
          <Link
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            href="/cardapio"
          >
            Cardapio do dia
          </Link>
          <Link
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            href="/app"
          >
            Vendas no app
          </Link>
          <Link
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            href="/suporte"
          >
            Central de suporte
          </Link>
          <Link
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            href="/wiki"
          >
            Wiki operacional
          </Link>
          <a
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft"
            href={adminUrl}
            target="_blank"
            rel="noreferrer"
          >
            Modulo de Gestao
          </a>
          <a
            className="rounded-md bg-graphite px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary"
            href={clientAreaUrl}
            target="_blank"
            rel="noreferrer"
          >
            Area do Cliente
          </a>
        </div>
      </section>
    </div>
  );
}

function HomeLetsFit({
  portalConfig,
  clientAreaUrl,
}: {
  portalConfig: PortalConfigPayload;
  clientAreaUrl: string;
}) {
  const content = resolveLetsFitContent(portalConfig);

  return (
    <div className="flex w-full flex-col">
      <HeroLetsFit {...content.hero} />
      <BenefitsBar items={content.benefits} />
      <Categories
        title={content.categories.title}
        subtitle={content.categories.subtitle}
        items={content.categories.items}
      />
      <KitSimulator {...content.kit} />
      <div className="my-16">
        <div className="mb-10 text-center">
          <h2 className="text-3xl font-bold text-text">{content.cardapio.title}</h2>
          <p className="mt-2 text-muted">{content.cardapio.subtitle}</p>
        </div>
        <CardapioList />
      </div>
      <section className="my-16 rounded-2xl border border-border bg-surface/70 p-6 md:p-8">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
          Integracao comercial
        </p>
        <h2 className="mt-2 text-2xl font-bold text-text">
          Vendas no app + suporte em um fluxo unico
        </h2>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
          O portal conecta descoberta de produtos, conversao no app e acompanhamento no
          suporte sem trocar de ecossistema.
        </p>
        <div className="mt-5 flex flex-wrap gap-3">
          <a
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft"
            href={clientAreaUrl}
            target="_blank"
            rel="noreferrer"
          >
            Abrir area de vendas (app)
          </a>
          <Link
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            href="/suporte"
          >
            Suporte
          </Link>
          <Link
            className="rounded-md border border-border bg-bg px-4 py-2 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
            href="/wiki"
          >
            Wiki
          </Link>
        </div>
      </section>
      <HowToHeat
        title={content.heat.title}
        subtitle={content.heat.subtitle}
        cards={content.heat.cards}
      />
      <Faq title={content.faq.title} items={content.faq.items} />
    </div>
  );
}

function HomeEditorial({
  portalConfig,
  clientAreaUrl,
}: {
  portalConfig: PortalConfigPayload;
  clientAreaUrl: string;
}) {
  const content = resolveLetsFitContent(portalConfig);
  const featuredCategories = content.categories.items ?? [];
  const editorialBenefits = content.benefits ?? [];

  return (
    <div className="space-y-8">
      <section className="overflow-hidden rounded-2xl border border-border bg-bg">
        <div className="grid gap-0 lg:grid-cols-[1.3fr_1fr]">
          <div className="p-6 md:p-8">
            <p className="inline-flex rounded-full border border-primary/30 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              {content.hero.kicker ?? "Edicao semanal"}
            </p>
            <h1 className="mt-4 text-3xl font-extrabold leading-tight text-text md:text-5xl">
              {content.hero.headline ?? "Cardapio autoral com ritmo de loja editorial"}
            </h1>
            <p className="mt-4 max-w-2xl text-sm leading-7 text-muted md:text-base">
              {content.hero.subheadline ??
                "Curadoria de marmitas em blocos visuais e fluxo direto para conversao no app."}
            </p>
            <div className="mt-6 flex flex-wrap gap-3">
              <a
                className="rounded-md bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary-soft"
                href={clientAreaUrl}
                target="_blank"
                rel="noreferrer"
              >
                Comprar no app
              </a>
              <Link
                className="rounded-md border border-border bg-bg px-5 py-3 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
                href="/cardapio"
              >
                Ver cardapio
              </Link>
              <Link
                className="rounded-md border border-border bg-bg px-5 py-3 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
                href="/suporte"
              >
                Suporte
              </Link>
            </div>
          </div>
          <div className="editorial-hero-panel border-l border-border p-6 md:p-8">
            <p className="text-xs font-semibold uppercase tracking-[0.14em] text-muted">
              Linha editorial
            </p>
            <div className="mt-4 space-y-3">
              {(editorialBenefits.length > 0
                ? editorialBenefits
                : [
                    { text: "Curadoria por objetivo alimentar" },
                    { text: "Conversao no app em fluxo unico" },
                    { text: "Suporte + wiki no mesmo ecossistema" },
                  ]
              ).map((item) => (
                <div
                  key={item.text}
                  className="rounded-lg border border-border bg-bg px-3 py-2 text-sm font-medium text-text"
                >
                  {item.text}
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        {(featuredCategories.length > 0
          ? featuredCategories
          : [
              { title: "Performance", description: "Proteina reforcada e rotina intensa." },
              { title: "Rotina", description: "Marmitas equilibradas para o dia a dia." },
              { title: "Leves", description: "Selecao de menor densidade calorica." },
              { title: "Kits", description: "Pacotes fechados para semana." },
            ]
        ).map((item) => (
          <article
            key={item.title}
            className="rounded-2xl border border-border bg-surface/70 p-5 transition hover:-translate-y-0.5 hover:border-primary/35"
          >
            <h2 className="text-lg font-bold text-text">{item.title}</h2>
            <p className="mt-2 text-sm text-muted">{item.description}</p>
          </article>
        ))}
      </section>

      <section className="rounded-2xl border border-border bg-surface/75 p-6 md:p-8">
        <div className="mb-8 flex flex-wrap items-end justify-between gap-3">
          <div>
            <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
              Curadoria diaria
            </p>
            <h2 className="mt-2 text-3xl font-bold text-text">
              {content.cardapio.title}
            </h2>
            <p className="mt-2 text-sm text-muted">{content.cardapio.subtitle}</p>
          </div>
          <a
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft"
            href={clientAreaUrl}
            target="_blank"
            rel="noreferrer"
          >
            Finalizar no app
          </a>
        </div>
        <CardapioList />
      </section>
    </div>
  );
}

export default async function HomePage() {
  const requestHeaders = await headers();
  const requestHostname = extractHostname(
    requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "",
  );
  const adminUrl = resolveFrontendUrl(requestHostname, 3002, ADMIN_URL);
  const clientAreaUrl = resolveFrontendUrl(requestHostname, 3001, CLIENT_AREA_URL);

  const portalConfig = await fetchPortalConfig("home");
  const template = portalConfig.active_template;

  if (template === "letsfit-clean") {
    return <HomeLetsFit portalConfig={portalConfig} clientAreaUrl={clientAreaUrl} />;
  }

  if (template === "editorial-jp") {
    return <HomeEditorial portalConfig={portalConfig} clientAreaUrl={clientAreaUrl} />;
  }

  return <HomeClassic adminUrl={adminUrl} clientAreaUrl={clientAreaUrl} />;
}

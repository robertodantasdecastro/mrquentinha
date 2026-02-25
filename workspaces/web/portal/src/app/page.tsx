import Link from "next/link";
import { Hero } from "@/components/Hero";
import { CardapioList } from "@/components/CardapioList";
import { HeroLetsFit, BenefitsBar, Categories, KitSimulator, HowToHeat, Faq } from "@/components/letsfit";

const ADMIN_URL = "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL = "https://app.mrquentinha.com.br";

function HomeClassic() {
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
            Pagina do App
          </Link>
          <a
            className="rounded-md bg-primary px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary-soft"
            href={ADMIN_URL}
            target="_blank"
            rel="noreferrer"
          >
            Modulo de Gestao
          </a>
          <a
            className="rounded-md bg-graphite px-4 py-2 text-sm font-semibold text-white transition hover:bg-primary"
            href={CLIENT_AREA_URL}
            target="_blank"
            rel="noreferrer"
          >
            Area do Cliente (Etapa 7)
          </a>
        </div>
      </section>
    </div>
  );
}

function HomeLetsFit() {
  return (
    <div className="flex flex-col w-full">
      <HeroLetsFit />
      <BenefitsBar />
      <Categories />
      <KitSimulator />
      <div className="my-16">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-text">Cardápio de Hoje</h2>
          <p className="text-muted mt-2">Peça até 11h para entrega no mesmo dia</p>
        </div>
        <CardapioList />
      </div>
      <HowToHeat />
      <Faq />
    </div>
  );
}

export default function HomePage() {
  const isLetsFit = process.env.NEXT_PUBLIC_PORTAL_TEMPLATE === "letsfit-clean";
  return isLetsFit ? <HomeLetsFit /> : <HomeClassic />;
}

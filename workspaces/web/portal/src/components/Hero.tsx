import Link from "next/link";

export function Hero() {
  return (
    <section className="relative overflow-hidden rounded-lg border border-border bg-surface/80 p-8 md:p-12">
      <div className="absolute -top-20 right-0 h-56 w-56 rounded-full bg-primary/18 blur-3xl" />
      <div className="absolute -bottom-24 left-10 h-48 w-48 rounded-full bg-graphite/15 blur-3xl" />

      <div className="relative max-w-3xl">
        <p className="inline-flex rounded-full border border-primary/40 bg-primary/10 px-3 py-1 text-xs font-semibold uppercase tracking-widest text-primary">
          www.mrquentinha.com.br
        </p>
        <h1 className="mt-5 text-3xl font-bold leading-tight text-text md:text-5xl">
          Alimentacao pratica com controle total do negocio.
        </h1>
        <p className="mt-4 max-w-2xl text-base leading-7 text-muted md:text-lg">
          O ecossistema Mr Quentinha conecta cliente, operacao e financeiro em uma
          plataforma unica para vender mais, reduzir desperdicio e manter padrao.
        </p>

        <div className="mt-8 flex flex-wrap gap-3">
          <Link
            href="/cardapio"
            className="rounded-md bg-primary px-5 py-3 text-sm font-semibold text-white transition hover:bg-primary-soft"
          >
            Ver cardapio do dia
          </Link>
          <Link
            href="/app"
            className="rounded-md border border-border bg-bg px-5 py-3 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
          >
            Baixar aplicativo
          </Link>
          <Link
            href="/contato"
            className="rounded-md border border-border bg-bg px-5 py-3 text-sm font-semibold text-text transition hover:border-primary hover:text-primary"
          >
            Falar com a equipe
          </Link>
        </div>
      </div>
    </section>
  );
}

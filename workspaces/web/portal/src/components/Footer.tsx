import Link from "next/link";

const ADMIN_URL = "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL = "https://app.mrquentinha.com.br";

export function Footer() {
  return (
    <footer className="border-t border-border bg-surface/70">
      <div className="mx-auto flex w-full max-w-6xl flex-col gap-5 px-4 py-10 md:flex-row md:items-center md:justify-between md:px-6">
        <div>
          <p className="text-base font-semibold text-text">Mr Quentinha</p>
          <p className="mt-1 text-sm text-muted">
            Marmitas com cardapio diario, planejamento de estoque e gestao completa.
          </p>
        </div>

        <div className="flex flex-wrap items-center gap-3 text-sm font-medium text-muted">
          <Link className="transition hover:text-primary" href="/">
            Home
          </Link>
          <Link className="transition hover:text-primary" href="/cardapio">
            Cardapio
          </Link>
          <Link className="transition hover:text-primary" href="/app">
            App
          </Link>
          <Link className="transition hover:text-primary" href="/contato">
            Contato
          </Link>
          <a className="transition hover:text-primary" href={ADMIN_URL} target="_blank" rel="noreferrer">
            Gestao
          </a>
          <a className="transition hover:text-primary" href={CLIENT_AREA_URL} target="_blank" rel="noreferrer">
            Area do Cliente
          </a>
        </div>
      </div>
    </footer>
  );
}

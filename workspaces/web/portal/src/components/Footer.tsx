import { AppFooter, Container } from "@mrquentinha/ui";
import Image from "next/image";
import Link from "next/link";

const ADMIN_URL = "https://admin.mrquentinha.com.br";
const CLIENT_AREA_URL = "https://app.mrquentinha.com.br";

export function Footer() {
  return (
    <AppFooter>
      <Container className="flex w-full flex-col gap-5 py-10 md:flex-row md:items-center md:justify-between">
        <div>
          <div className="inline-flex rounded-lg bg-white/95 px-2 py-1 ring-1 ring-border/70 shadow-sm dark:bg-white">
            <Image
              src="/brand/original_png/logo_wordmark_original.png"
              alt="Mr Quentinha"
              width={176}
              height={67}
            />
          </div>
          <p className="mt-2 text-sm text-muted">
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
      </Container>
    </AppFooter>
  );
}

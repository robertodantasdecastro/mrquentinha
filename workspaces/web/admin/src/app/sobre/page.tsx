export default function SobrePage() {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-text">Sobre</h1>
        <p className="mt-2 text-sm text-muted">
          Informacoes de contato do desenvolvimento e suporte tecnico do ecossistema Mr Quentinha.
        </p>
      </section>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-text">Contato do desenvolvedor</h2>
        <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-[180px_1fr]">
          <dt className="font-medium text-text">Nome</dt>
          <dd className="text-muted">Roberto Dantas de Castro</dd>

          <dt className="font-medium text-text">E-mail</dt>
          <dd className="text-muted">robertodabtasdecastro@gmail.com</dd>

          <dt className="font-medium text-text">GitHub</dt>
          <dd className="text-muted">
            <a
              href="https://github.com/robertodantasdecastro/mrquentinha"
              target="_blank"
              rel="noopener noreferrer"
              className="text-primary underline-offset-2 hover:underline"
            >
              github.com/robertodantasdecastro/mrquentinha
            </a>
          </dd>
        </dl>
      </section>
    </div>
  );
}

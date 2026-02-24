export const metadata = {
  title: "Contato",
  description: "Canal institucional de contato do Mr Quentinha.",
};

export default function ContatoPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
          Fale conosco
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">Contato institucional</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
          Para parcerias, suporte comercial e implantacao do ecossistema Mr Quentinha.
        </p>
      </section>

      <section className="grid gap-4 md:grid-cols-2">
        <article className="rounded-lg border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Atendimento</h2>
          <p className="mt-3 text-sm text-muted">contato@mrquentinha.com.br</p>
          <p className="mt-2 text-sm text-muted">+55 (11) 90000-0000</p>
        </article>

        <article className="rounded-lg border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">Horario comercial</h2>
          <p className="mt-3 text-sm text-muted">Segunda a sexta, das 08h as 18h</p>
          <p className="mt-2 text-sm text-muted">Sao Paulo - SP</p>
        </article>
      </section>
    </div>
  );
}

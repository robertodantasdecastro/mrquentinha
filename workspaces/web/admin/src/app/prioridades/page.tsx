export default function PrioridadesPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h1 className="text-2xl font-bold text-text">Prioridades da semana</h1>
        <p className="mt-2 text-sm text-muted">
          Ritmo de entrega e foco por etapa, com rastreio do impacto operacional.
        </p>
      </section>

      <section className="rounded-2xl border border-border bg-surface/80 p-6 shadow-sm">
        <h2 className="text-lg font-semibold text-text">Fila cronologica</h2>
        <ol className="mt-3 list-decimal space-y-2 pl-5 text-sm text-muted">
          <li>Executar T9.1.2 com relatorios integrados e exportacao CSV.</li>
          <li>Refinar UX/IX do Admin com hotpages, menus contextuais e graficos.</li>
          <li>Integrar Portal CMS no portal (T6.3.2) sem conflito com Antigravity.</li>
          <li>Preparar fluxo de pagamentos online (T7.2).</li>
        </ol>
      </section>
    </div>
  );
}

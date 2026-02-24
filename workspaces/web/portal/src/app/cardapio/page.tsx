import { CardapioList } from "@/components/CardapioList";

export const metadata = {
  title: "Cardapio",
  description: "Consulta do cardapio por data em tempo real.",
};

export default function CardapioPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
          API ao vivo
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">Cardapio do dia</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
          Selecione a data para consultar itens e precos atualizados direto do backend.
        </p>
      </section>

      <CardapioList />
    </div>
  );
}

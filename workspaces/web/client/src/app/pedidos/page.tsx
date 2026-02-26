import { OrderHistoryList } from "@/components/OrderHistoryList";

export default function PedidosPage() {
  return (
    <section className="space-y-4">
      <header className="rounded-2xl border border-border bg-surface/70 p-5">
        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-primary">
          Meus pedidos
        </p>
        <h1 className="mt-1 text-2xl font-bold text-text">Acompanhe seu historico</h1>
        <p className="mt-2 text-sm text-muted">
          Do login ao recebimento: acompanhe status de preparo, entrega e confirme o recebimento aqui.
        </p>
      </header>

      <OrderHistoryList />
    </section>
  );
}

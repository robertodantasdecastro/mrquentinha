import { QRDownloadCard } from "@/components/QRDownloadCard";

export const metadata = {
  title: "App",
  description: "Pagina oficial para download do aplicativo Mr Quentinha.",
};

export default function AppPage() {
  return (
    <div className="space-y-6">
      <section className="rounded-lg border border-border bg-bg p-6">
        <p className="text-xs font-semibold uppercase tracking-[0.16em] text-primary">
          Mobile
        </p>
        <h1 className="mt-2 text-3xl font-bold text-text">Baixe o app Mr Quentinha</h1>
        <p className="mt-3 max-w-3xl text-sm leading-6 text-muted md:text-base">
          Escaneie o QR Code ou use os botoes para baixar no Android e iOS.
        </p>
      </section>

      <QRDownloadCard />
    </div>
  );
}

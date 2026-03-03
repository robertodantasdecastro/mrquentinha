import { headers } from "next/headers";

import { PortalPageIntro } from "@/components/PortalPageIntro";
import { QRDownloadCard } from "@/components/QRDownloadCard";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";
import { extractHostname, resolveFrontendUrl } from "@/lib/networkHost";
import { fetchPortalAppDownloads } from "@/lib/mobileRelease";
import { fetchPortalConfig } from "@/lib/portalTemplate";

const CLIENT_AREA_URL =
  process.env.NEXT_PUBLIC_CLIENT_AREA_URL?.trim() || "https://app.mrquentinha.com.br";

export const metadata = {
  title: "App",
  description: "Pagina oficial para download do aplicativo Mr Quentinha.",
};

export default async function AppPage() {
  const requestHeaders = await headers();
  const requestHostname = extractHostname(
    requestHeaders.get("x-forwarded-host") || requestHeaders.get("host") || "",
  );
  const clientAreaUrl = resolveFrontendUrl(requestHostname, 3001, CLIENT_AREA_URL);
  const downloads = await fetchPortalAppDownloads();
  const portalConfig = await fetchPortalConfig("app");
  const heroBody = asObject(resolveSectionByKey(portalConfig.sections, "hero")?.body_json);

  return (
    <div className="space-y-6">
      <PortalPageIntro
        kicker={asString(heroBody.kicker, "Canal de vendas")}
        title={asString(heroBody.headline, "App e Web Cliente no mesmo fluxo comercial")}
        description={asString(
          heroBody.subheadline,
          "A venda acontece no app.mrquentinha.com.br, com jornada de pedido, pagamento e acompanhamento em tempo real. Aqui voce tambem encontra os downloads mobile.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Abrir area de vendas (app)", href: clientAreaUrl, external: true, tone: "primary" },
          { label: "Central de suporte", href: "/suporte", tone: "ghost" },
          { label: "Wiki operacional", href: "/wiki", tone: "soft" },
        ]}
      />

      <section className="grid gap-4 md:grid-cols-3">
        <article className="rounded-lg border border-border bg-surface/70 p-5 md:col-span-2">
          <h2 className="text-lg font-semibold text-text">Integracao Portal + App</h2>
          <p className="mt-2 text-sm leading-6 text-muted">
            O portal concentra descoberta e comunicacao institucional. O app do cliente
            concentra conversao de vendas, historico de pedidos e suporte autenticado.
          </p>
        </article>
        <article className="rounded-lg border border-border bg-surface/70 p-5">
          <h2 className="text-lg font-semibold text-text">URL oficial</h2>
          <p className="mt-2 break-all text-sm text-muted">{clientAreaUrl}</p>
        </article>
      </section>

      <QRDownloadCard
        appUrl={downloads.appUrl}
        androidDownloadUrl={downloads.androidDownloadUrl}
        iosDownloadUrl={downloads.iosDownloadUrl}
        releaseVersion={downloads.releaseVersion}
        publishedAt={downloads.publishedAt}
      />
    </div>
  );
}

import { ClientPageIntro } from "@/components/ClientPageIntro";
import { SupportCenter } from "@/components/SupportCenter";
import { fetchClientConfig } from "@/lib/clientTemplate";
import { asObject, asString, resolveSectionByKey } from "@/lib/portalContent";

const PORTAL_SUPPORT_URL =
  process.env.NEXT_PUBLIC_PORTAL_URL?.trim() || "https://www.mrquentinha.com.br/suporte";

export const metadata = {
  title: "Suporte",
  description: "Central de suporte do Web Cliente Mr Quentinha.",
};

export default async function SuportePage() {
  const config = await fetchClientConfig("suporte");
  const heroBody = asObject(resolveSectionByKey(config.sections, "hero")?.body_json);

  return (
    <div className="space-y-4">
      <ClientPageIntro
        kicker={asString(heroBody.kicker, "Atendimento")}
        title={asString(heroBody.headline, "Suporte do cliente")}
        description={asString(
          heroBody.subheadline,
          "Abra chamados, acompanhe respostas e mantenha historico de atendimento no seu login.",
        )}
        imageUrl={asString(heroBody.image_url)}
        actions={[
          { label: "Entrar na conta", href: "/conta?next=/suporte", tone: "primary" },
          { label: "Wiki de ajuda", href: "/wiki", tone: "ghost" },
          { label: "Suporte institucional", href: PORTAL_SUPPORT_URL, external: true, tone: "soft" },
        ]}
      />

      <SupportCenter />
    </div>
  );
}
